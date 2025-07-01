import logging
import re
import pandas as pd
import os
import asyncio
from libs.github import repo
from libs.rate_limiter import rate_limited_github
from libs.task_queue import github_task_queue
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

issue_url_pattern = re.compile(r"- \[x\] https://github\.com/Expensify/App/issues/(\d+)")


@rate_limited_github
def _get_deploy_checklist_issues():
    """Get deploy checklist issues with rate limiting."""
    return repo.get_issues(state="closed", labels=["StagingDeployCash"])


@rate_limited_github
def _search_prs_for_date_range(query_range: str, page: int):
    """Search PRs for a specific date range with rate limiting."""
    query = f"repo:Expensify/App is:pr is:merged merged:{query_range}"
    url = f"/search/issues?q={query}&per_page=100&page={page}"
    return repo._requester.requestJsonAndCheck("GET", url)


async def run():
    deploy_checklist = _get_deploy_checklist_issues()
    deploy_blockers_data = []

    count = 0
    for checklist in deploy_checklist:
        body = checklist.body or ""
        if "Deploy Blockers:" not in body:
            count += 1
            yield "No deploy blockers found in the issue body. for issue: " + checklist.html_url
            continue

        try:
            blockers_section = body.split("Deploy Blockers:")[1].split("Deployer verifications:")[0]
        except IndexError:
            continue

        matches = issue_url_pattern.findall(blockers_section)
        if not matches:
            yield "No issue URLs found in blockers section."
            continue

        for issue_number in matches:
            issue_url = f"https://github.com/Expensify/App/issues/{issue_number}"
            deploy_blockers_data.append(
                {
                    "Deploy Blocker Issue Number": issue_number,
                    "Deploy Blocker GitHub URL": issue_url,
                    "StagingDeployCash Issue": checklist.title,
                    "StagingDeployCash Issue Number": checklist.number,
                    "StagingDeployCash GitHub URL": checklist.html_url,
                    "StagingDeployCash Created At": checklist.created_at.strftime("%Y-%m-%d"),
                }
            )
    yield f"Processed deploy checklists."
    yield f"Total deploy checklists without blocker: {count}"
    if deploy_blockers_data:
        yield f"Found {len(deploy_blockers_data)} deploy blockers."
        df = pd.DataFrame(deploy_blockers_data)
        df.to_csv("deploy_blockers.csv", index=False)
        yield f"Saved {len(df)} deploy blockers to deploy_blockers.csv"


async def get_historical_prs():
    output_file = "merged_cp_staging_prs.csv"
    total_saved = 0

    # Start date and how many months to loop
    start = datetime(2021, 1, 1)
    slices = 50

    for _ in range(slices):
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        query_range = f"{start.date()}..{end.date()}"
        print(f"\n📅 Fetching merged PRs for: {query_range}")

        page = 1
        while True:
            try:
                result = _search_prs_for_date_range(query_range, page)
                items = result[1].get("items", [])

                if not items:
                    break

                pr_data = []
                for item in items:
                    title = item["title"].lower()
                    labels = [label["name"].lower() for label in item.get("labels", [])]

                    if "revert" not in title and "cp staging" not in labels:
                        continue

                    pr_data.append(
                        {
                            "PR Number": item["number"],
                            "PR Title": item["title"],
                            "PR URL": item["html_url"],
                            "Merged At": (item["closed_at"][:10] if item.get("closed_at") else ""),
                        }
                    )

                if pr_data:
                    df = pd.DataFrame(pr_data)
                    df.to_csv(
                        output_file,
                        mode="a",
                        header=not os.path.exists(output_file),
                        index=False,
                    )
                    print(f"  ✅ Appended {len(df)} PRs from page {page}")
                    total_saved += len(df)

                page += 1
                if page > 10:
                    print(" ⚠️ Hit GitHub Search API 1000-item limit for this month. Moving on.")
                    break

                # Rate limiting handled by decorator, but add small delay between pages
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error fetching PRs for {query_range}, page {page}: {e}")
                break

        # Advance to next month
        start = (start.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Small delay between months
        await asyncio.sleep(1)

    print(f"\n🎉 Done! Total PRs saved: {total_saved}")


async def get_all_merged_prs():
    output_file = "merged_all_prs.csv"
    total_saved = 0

    start = datetime(2023, 4, 1)
    slices = 60

    for _ in range(slices):
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        query_range = f"{start.date()}..{end.date()}"
        print(f"\n📅 Fetching merged PRs for: {query_range}")

        page = 1
        while True:
            try:
                result = _search_prs_for_date_range(query_range, page)
                items = result[1].get("items", [])

                if not items:
                    break

                pr_data = []
                for item in items:
                    if item.get("user", {}).get("login", "").lower() == "osbotify":
                        continue

                    pr_data.append(
                        {
                            "PR Number": item["number"],
                            "PR Title": item["title"],
                            "PR URL": item["html_url"],
                            "Merged At": (item["closed_at"][:10] if item.get("closed_at") else ""),
                        }
                    )

                if pr_data:
                    df = pd.DataFrame(pr_data)
                    df.to_csv(
                        output_file,
                        mode="a",
                        header=not os.path.exists(output_file),
                        index=False,
                    )
                    print(f"  ✅ Appended {len(df)} PRs from page {page}")
                    total_saved += len(df)

                page += 1
                if page > 10:
                    print("⚠️ Hit GitHub Search API 1000-item limit for this month. Moving on.")
                    break

                # Rate limiting handled by decorator, but add small delay between pages
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Error fetching PRs for {query_range}, page {page}: {e}")
                break

        # Advance to next month
        start = (start.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Small delay between months
        await asyncio.sleep(1)

    print(f"\n🎉 Done! Total PRs saved: {total_saved}")
