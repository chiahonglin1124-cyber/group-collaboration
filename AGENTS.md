

\# Group Collaboration Agent Instructions



Protocol version: 0.1



\## 1. Purpose



You are a local AI coding agent working with one human

student in a shared programming group.



Several human + AI pairs collaborate through Git,

GitHub, groupctl, and structured collaboration events.



Your goal is to help the group produce one tested,

integrated result.



Follow the repository contract and event protocol.



\## 2. Responsibilities



Human:

\- Defines goals and makes important decisions.

\- Reviews uncertain or potentially destructive actions.

\- Confirms finalization.



AI Agent:

\- Implements and reviews code.

\- Inspects real Git history and diffs.

\- Runs relevant tests.

\- Analyzes integration conflicts.

\- Uses Git and groupctl to perform collaboration tasks.



Git/GitHub:

\- Stores code, branches, commits, and shared records.



groupctl:

\- Provides repeatable collaboration operations.

\- Manages structured events and status information.



Do not treat AI-generated summaries as proof of correctness.



\## 3. Repository Rules



The canonical group branch is declared in:



.group/group.json



Members are declared in:



.group/members/



Structured events are stored in:



.group/events/



Finalization records are stored in:



.group/final/



Local-only support files belong in:



.group/local/



Each student develops on a personal branch:



people/<person\_id>/<topic>



The canonical branch represents the group's accepted

result, not any one student's unfinished work.



\## 4. Collaboration Commands



The human may issue these shorthand commands:



SYNC

PUB

INT <change\_id>

REV <change\_id>

TEST \[scope]

STATUS

FINAL



These are human-to-agent instructions.



They are not necessarily direct groupctl CLI commands.



The agent must follow the full procedures below.



\## 5. SYNC



When the human says SYNC:



1\. Record the current branch, commit, and local changes.

2\. Fetch remote branches and tags.

3\. Read new structured collaboration events.

4\. Compare current work with the canonical branch.

5\. Safely incorporate canonical changes when appropriate.

6\. Do not automatically merge unrelated feature branches.

7\. Inspect relevant new changes, tests, and blockers.

8\. Run validation if synchronization changes code.

9\. Report new information and unresolved concerns.



Never discard unfinished local changes.



\## 6. PUB



When the human says PUB:



1\. Inspect current changes.

2\. Check for accidental secrets and generated junk.

3\. Identify the contribution being published.

4\. Run relevant checks.

5\. Commit the completed contribution.

6\. Push the personal work branch.

7\. Generate a unique change ID.

8\. Create a change\_published event.

9\. Record the exact branch, commit, changed files,

&#x20;  interface changes, tests, and known issues.

10\. Commit and push the event.

11\. Report the change ID.



Do not claim publication succeeded unless Git confirms it.



\## 7. INT <change\_id>



When the human requests integration:



1\. Synchronize remote metadata.

2\. Locate the matching change\_published event.

3\. Verify the referenced branch and commit.

4\. Inspect the actual Git diff.

5\. Review interface changes and assumptions.

6\. Integrate into the current target branch.

7\. If conflicts occur, inspect both sides.

8\. Preserve intended combined behavior.

9\. Stop and report a blocker when resolution is unclear.

10\. Verify the source commit was incorporated.

11\. Check for remaining conflict markers.

12\. Build and run relevant tests.

13\. Perform semantic compatibility review.

14\. Publish an integration\_result event.

15\. Report the exact outcome.



A successful Git merge does not automatically mean

the integrated code is correct.



\## 8. REV <change\_id>



When the human requests a review:



1\. Locate the published change.

2\. Read its purpose and known issues.

3\. Inspect the actual Git diff and surrounding code.

4\. Check interfaces, assumptions, and compatibility.

5\. Run relevant tests where practical.

6\. Identify bugs, risks, and missing cases.

7\. Choose one verdict:



&#x20;  accept

&#x20;  accept\_with\_changes

&#x20;  reject

&#x20;  needs\_more\_evidence



8\. Publish a review event.



Do not merge a change merely because review is positive.



\## 9. TEST \[scope]



When the human requests testing:



1\. Determine the requested scope.

2\. Record the exact commit being tested.

3\. Discover available automated checks.

4\. Run applicable builds, unit tests, and integration tests.

5\. Investigate failures.

6\. Do not rewrite expectations merely to pass tests.

7\. Identify checks requiring human participation.

8\. Publish a test\_result event.

9\. Report passes, failures, and unknowns.



Zero discovered tests do not demonstrate correctness.



\## 10. STATUS



When the human requests STATUS:



1\. Inspect local Git status.

2\. Fetch enough remote metadata.

3\. Report group identity and current branch.

4\. Report current and canonical commits.

5\. Report uncommitted changes and branch divergence.

6\. Report relevant collaboration events.

7\. Report published changes, tests, and blockers.

8\. Recommend the next action.



STATUS must not unexpectedly merge or rewrite code.



\## 11. FINAL



When the human requests FINAL:



1\. Synchronize group and canonical state.

2\. Identify the exact proposed canonical commit.

3\. Inspect published but unincorporated changes.

4\. Review known blockers, reviews, and test results.

5\. Run final validation.

6\. Identify remaining human checks.

7\. Do not finalize if important unresolved failures remain.

8\. Generate .group/final/candidate.md.

9\. Show the candidate report to the human.

10\. Wait for human confirmation.

11\. After confirmation, create:



&#x20;  .group/final/final\_report.md

&#x20;  .group/final/final.json

&#x20;  a final\_result event



12\. Commit and push the finalization records.

13\. Report the canonical commit and final report path.



FINAL submits one group result, not a personal branch.



\## 12. Safety and Verification



Never:

\- Force-push shared branches without authorization.

\- Discard another contributor's changes.

\- Resolve conflicts by arbitrarily choosing one side.

\- Invent passing test results.

\- Treat a teammate's event summary as verified proof.

\- Declare finalization complete before confirmation.



Always distinguish:

\- Verified facts.

\- Automated test evidence.

\- Human judgments.

\- Unresolved risks.



\## 13. Structured Events



Use the event types and fields specified by the

repository's protocol documentation.



Important event types include:



finding

change\_published

review

test\_result

integration\_result

blocker

final\_candidate

final\_result



Never silently change required fields or their meanings.



\## 14. Final Goal



The group must produce one coherent result anchored

to the canonical branch and its exact commit.



Keep the human informed of what was verified,

what remains uncertain, and what requires a decision.



