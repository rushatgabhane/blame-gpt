import './App.css';

function App() {
  return (
    <div id="main">
      <h1 style={{ marginBottom: '20px', marginTop: '80px' }}>BlameGPT</h1>
      <p>Finds the pull request begging to be reverted. Fast. </p>
      <h2 id="software">Why is my shiny new feature not on production yet?</h2>
      <p>Oh... we have deploy blockers!!</p>
      <p>
        BlameGPT finds the PR causing a deploy blocker so you can go back to
        shipping. (Blame the PR, not your coworker. Probably.)
      </p>
      <p>BlameGPT requires zero config.</p>
      <p>
        For a <span style={{ fontWeight: 'bold' }}>demo</span>, reach out on{' '}
        <a href="mailto:rushatgabhane@gmail.com">[rushatgabhane@gmail.com]</a>
      </p>
      <h2>Demo</h2>
      <p>
        Possible culprit PRs for issue -{' '}
        <a href="https://github.com/Expensify/App/issues/62685">
          Expense - Next step action shows skeleton loading when workflows are
          disabled
        </a>
      </p>
      <ul>
        <li>
          <p>
            <a href="https://github.com/Expensify/App/pull/62363">PR #62363</a>:
            This PR adds loading skeletons for Next steps and Report Actions in
            report screens, which could be related to the skeleton loading issue
            when the workflows are disabled after submitting an expense.
          </p>
        </li>
        <li>
          <p>
            <a href="https://github.com/Expensify/App/pull/58020">PR #58020</a>:
            This PR changes components related to report actions and includes
            the MoneyReportHeader component, which may impact the displaying of
            next step actions after submitting an expense.
          </p>
        </li>
        <li>
          <p>
            <a href="https://https://github.com/Expensify/App/pull/61170">
              PR #61170
            </a>
            : This PR introduces changes to report action items and could
            influence the visibility and interactions with the expense
            submission process.
          </p>
        </li>
      </ul>
    </div>
  );
}

export default App;
