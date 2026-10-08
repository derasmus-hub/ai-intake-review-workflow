\# Project Instructions



This is a public portfolio project.



The goal is to demonstrate how AI can be integrated into a normal business workflow while keeping a human in control of important decisions.



\## Working rules



1\. Work only inside this repository.



2\. Do not commit or push to GitHub unless explicitly instructed.



3\. Keep the architecture simple enough to explain clearly in a technical interview.



4\. For the first version, do not use a real AI API.



5\. Use deterministic mock classification for the first version.



6\. Do not add PostgreSQL, n8n, a frontend, or production deployment unless explicitly requested.



7\. The AI classification layer must not directly approve or reject a request.



8\. Human review must control the final workflow decision.



9\. Use clear workflow states and explicit state transitions.



10\. Run relevant tests before reporting a task complete.



11\. Do not invent customers, production usage, performance statistics, or business results.



12\. Do not reference private Erasmus Labs projects or private security system architecture.



\## Execution environment



The repository is edited from Windows.



Python and test execution must happen inside the Docker container named:



ai-intake-dev



The repository is mounted inside that container at:



/workspace



Use commands such as:



docker exec ai-intake-dev python ...

docker exec ai-intake-dev pytest

docker exec ai-intake-dev sh -lc "..."



Do not create or use a Windows .venv for this project.



\## Completion report



After completing a task, report:



1\. Files changed

2\. Architecture or logic changed

3\. Tests run

4\. Test results

5\. Manual verification performed

6\. Anything incomplete

