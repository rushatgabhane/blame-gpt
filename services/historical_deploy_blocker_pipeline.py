import logging
import re
import pandas as pd
from libs.github import repo_secondary

logger = logging.getLogger(__name__)

issue_url_pattern = re.compile(
    r"- \[x\] https://github\.com/Expensify/App/issues/(\d+)"
)


async def run():
    deploy_checklist = repo_secondary.get_issues(
        state="closed", labels=["StagingDeployCash"]
    )
    deploy_blockers_data = []

    count = 0
    for checklist in deploy_checklist:
        body = checklist.body or ""
        if "Deploy Blockers:" not in body:
            count += 1
            yield "No deploy blockers found in the issue body. for issue: " + checklist.html_url
            continue

        try:
            blockers_section = body.split("Deploy Blockers:")[1].split(
                "Deployer verifications:"
            )[0]
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
                    "StagingDeployCash Created At": checklist.created_at.strftime(
                        "%Y-%m-%d"
                    ),
                }
            )
    yield f"Processed deploy checklists."
    yield f"Total deploy checklists without blocker: {count}"
    if deploy_blockers_data:
        yield f"Found {len(deploy_blockers_data)} deploy blockers."
        df = pd.DataFrame(deploy_blockers_data)
        df.to_csv("deploy_blockers.csv", index=False)
        yield f"Saved {len(df)} deploy blockers to deploy_blockers.csv"
