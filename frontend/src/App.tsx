import './App.css';

function App() {
  return (
    <div id="main">
      <h1 style={{ marginBottom: '20px', marginTop: '80px' }}>Blame GPT</h1>
      <p>Finds the PRs begging to be reverted. Fast. </p>
      <h2 id="software">Why is my shiny new feature not on production yet?</h2>
      <p>Oh... we have deploy blockers!!</p>
      <p>
        BlameGPT finds the PR causing a deploy blocker so you can go back to
        shipping. (Blame the PR, not your coworker. Probably.)
      </p>
      <p>
        BlameGPT requires zero config. Reach out on{' '}
        <a href="mailto:rushatgabhane@gmail.com">[rushatgabhane@gmail.com]</a>
      </p>
    </div>
  );
}

export default App;
