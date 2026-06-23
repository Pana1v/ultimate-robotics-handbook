---
description: The courses, books, communities, and competitions actually worth your hours - and how to stay current without drowning
icon: globe-pointer
---

# External Resources & Communities

This handbook is deliberately opinionated, and so is this page. The internet has ten thousand robotics resources; maybe thirty are worth your time. These are the ones I keep coming back to, recommend to juniors, and have personally used. If something isn't listed, it's either because I haven't vetted it or because it didn't survive contact with a real robot.

## Courses worth your time

| Course | Who / where | Why it's worth it |
| --- | --- | --- |
| **Underactuated Robotics** | Russ Tedrake, MIT - free at [underactuated.mit.edu](https://underactuated.mit.edu) | The best dynamics-and-control course in existence. Trajectory optimization, LQR, Lyapunov, legged locomotion - with runnable notebooks. Lecture videos are on YouTube every year. |
| **Robotic Manipulation** | Tedrake again - [manipulation.csail.mit.edu](https://manipulation.csail.mit.edu) | The manipulation counterpart. Geometric perception, grasping, and (recent editions) learned policies. Same format: free text + notebooks + lectures. |
| **Cyrill Stachniss lectures** | University of Bonn - [YouTube channel](https://www.youtube.com/@CyrillStachniss) | Full university courses on SLAM, mobile sensing, and photogrammetry, uploaded in their entirety. The graph SLAM and least-squares lectures are the clearest treatment anywhere. Watch these alongside our [filter SLAM](../slam-and-state-estimation/filter-slam.md) page. |
| **Probabilistic Robotics (the course form)** | Stachniss / Burgard lineage at Freiburg and Bonn | The book (below) has no official course, but Stachniss's SLAM course *is* the video companion - same Bayes filter, EKF, particle filter, graph SLAM arc. |
| **Visual SLAM** | Gao Xiang's *slambook* + TUM's Multiple View Geometry (Cremers) | The slambook ("Introduction to Visual SLAM: From Theory to Practice", free on GitHub with code) takes you from epipolar geometry to a working stereo VO. Cremers' MVG lectures give the rigorous geometry underneath. Pair with our [visual SLAM](../slam-and-state-estimation/visual-slam.md) page. |
| **Modern Robotics (Coursera)** | Lynch & Park, Northwestern | Screw theory, forward/inverse kinematics, dynamics. Slower-paced than the book; good if you want graded structure. |

My honest ordering: if you can only do one, do Underactuated. It changes how you think about every controller you write afterwards.

How to sequence them depending on where you're coming from:

* **From software engineering** - Modern Robotics first (you need the kinematics vocabulary), then Stachniss's SLAM course, then Underactuated.
* **From mechanical/electrical engineering** - you likely have the dynamics; go straight to Stachniss and the slambook, because state estimation is the gap.
* **From ML** - Underactuated first. The biggest failure mode of ML people entering robotics is treating the robot as a dataset generator instead of a dynamical system.

What I'd skip: most paid "become a robotics engineer" bootcamps. The free material above is strictly better, and employers know it. Also skip passive video-binging - none of these courses work without doing the exercises. Tedrake's notebooks run in a browser; there is no excuse.

## Books that survive contact with practice

Most robotics books are reference-shaped - you don't read them, you raid them. These four I have actually read cover to cover and still raid:

* **Probabilistic Robotics** - Thrun, Burgard, Fox (2005). Still *the* book for state estimation 20 years later. The notation is dated and the code examples are pseudocode, but the Bayes filter chapters are the foundation everything in our [SLAM section](../slam-and-state-estimation/filter-slam.md) builds on. Read chapters 2-8, skim the rest.
* **Modern Robotics** - Lynch & Park. Free PDF from the authors. The product-of-exponentials formulation is cleaner than the DH-parameter approach older books push, and it's what modern manipulation code actually uses. The accompanying library exists in Python, MATLAB, and C++.
* **A Philosophy of Software Design** - John Ousterhout. Not a robotics book, which is exactly why robotics engineers need it. Robot codebases die from complexity, not from bad math. "Define errors out of existence" alone will improve your node code more than any ROS tutorial.
* **State Estimation for Robotics** - Tim Barfoot. Free PDF from the author. Where Probabilistic Robotics stops (Lie groups, batch estimation, continuous-time trajectories), Barfoot starts. Read it when filter notation stops being enough.

A rule I hold to: a book earns shelf space when you reach for it *during* a debugging session, not before one. All four above pass.

**The reference shelf** - books you raid rather than read:

* **Planning Algorithms** - Steven LaValle. Free online. Encyclopedic coverage of motion planning; the RRT chapters come straight from the source (LaValle invented RRTs).
* **Multiple View Geometry in Computer Vision** - Hartley & Zisserman. *The* geometry reference for anything camera-shaped. Dense; raid it via the index.
* **Robotics, Vision and Control** - Peter Corke. The friendliest bridge between theory and runnable code, with companion toolboxes in MATLAB and Python.
* **Reinforcement Learning: An Introduction** - Sutton & Barto. Free PDF. If you touch RL at all, you need the first ten chapters as shared vocabulary - see our [modern RL](../robot-learning/reinforcement-learning-modern.md) page for what came after.

## Blogs, YouTube channels, newsletters

I'm naming fewer here on purpose - dead blogs and abandoned channels are the norm, and I'd rather list five live sources than twenty stale ones.

* **Weekly Robotics** ([weeklyrobotics.com](https://www.weeklyrobotics.com)) - Mat Sadowski's curated newsletter. Running for years, still active as of mid-2026. The single best low-effort way to keep peripheral vision on the field.
* **IEEE Spectrum robotics** - Evan Ackerman's coverage and the long-running *Video Friday* roundup. Journalism, not hype.
* **Articulated Robotics** (Josh Newans, YouTube) - the best practical ROS 2 series available. His "build a mobile robot" arc is what I point people at instead of the official tutorials.
* **Cyrill Stachniss's channel** - listed above under courses, but it doubles as a "paper explained" feed; he regularly uploads short breakdowns of recent SLAM and photogrammetry work.
* **The Robot Report** - industry news, funding, product launches. Useful for the commercial side that arXiv won't show you.

Company engineering blogs (Boston Dynamics, Skydio, Physical Intelligence, and friends) are worth reading when they publish, but they publish irregularly - treat them as occasional treats, not a feed.

Podcasts exist in robotics but turnover is high and I won't vouch for any specific one staying alive; check what's currently active before subscribing.

## Communities

* **ROS Discourse** ([discourse.ros.org](https://discourse.ros.org)) - the official ROS community forum. Release announcements, REP discussions, working groups. If you ship ROS 2 professionally, you should at least lurk here; breaking changes get discussed months before they land.
* **Robotics Stack Exchange** ([robotics.stackexchange.com](https://robotics.stackexchange.com)) - absorbed the old ROS Answers in 2023. The right place for "why is my TF tree broken" questions. Search before asking; your question has been asked.
* **r/robotics** - high noise, occasional gold. Good for hardware sourcing questions and career threads; bad for deep technical answers. r/ROS is smaller and more focused.
* **Discord servers** - the most active one I can vouch for is the **LeRobot Discord** (linked from the [LeRobot GitHub](https://github.com/huggingface/lerobot)), which has become the de facto hangout for low-cost manipulation and imitation learning - the same ecosystem our [imitation learning](../robot-learning/imitation-learning.md) page covers. Plenty of other robotics Discords exist; quality varies too much for blanket recommendations.

Two things people overlook:

* **GitHub issue trackers are communities.** The issues and discussions on Nav2, MoveIt, slam_toolbox, and LeRobot are where the deepest technical conversations in the field happen. Reading closed issues on a package you depend on is criminally underrated debugging.
* **ROSCon and its local chapters.** The yearly ROSCon (and regional ROSCon events) talks are all recorded and freely available. The hallway track is the real product though - if one happens near you, go.

One opinion from experience: asking a well-formed question with a minimal reproduction on ROS Discourse or Stack Exchange gets answered surprisingly often by the actual maintainers. The bottleneck is almost always the quality of the question, not the community.

## Competitions to actually enter

Competitions compress years of "it works in theory" lessons into months. Deadlines force integration, and integration is where robotics actually lives.

| Competition | Who it's for | What you'll learn |
| --- | --- | --- |
| **FIRST (FRC/FTC) / VEX** | School and early university students | Mechanical design, basic control, teamwork under deadline. The classic on-ramp - many working roboticists started here. |
| **RoboCup** | University teams | Pick your league: Soccer (multi-agent, perception under motion), @Home (mobile manipulation, the hardest one in my view), Rescue, Industrial. Real autonomy, no remote control. |
| **BARN Challenge** (ICRA) | Individuals or small teams with ROS experience | Navigation in procedurally generated, brutally constrained environments. 300 randomized worlds expose every weakness in your planner. I competed in it - write-up at [BARN Challenge](../authors-projects/barn-challenge.md). Low barrier to entry: it runs in Gazebo, and a solo entrant can be competitive. |
| **Eurobot** | European student/amateur teams | Themed table-top autonomous matches, new rules yearly. Strong mechanical and embedded focus; great if your weakness is hardware. |
| **F1TENTH** | University teams, individuals | 1/10-scale autonomous racing. Teaches you what "real-time" actually means when the wall arrives at 7 m/s. |

If you're past student age and employed, BARN and F1TENTH are the realistic options - both can be done solo, in simulation, on evenings and weekends. That's not hypothetical; it's how I did it.

Advice for a first entry, in order of importance:

1. **Submit something bad early.** A baseline on the leaderboard beats a brilliant architecture on your laptop. You learn the evaluation harness, which is half the battle.
2. **Read past winners' write-ups before designing anything.** Most competitions have a graveyard of approaches that sound good and score poorly; don't rediscover it.
3. **Budget more time for infrastructure than algorithms.** Containerizing your stack, automating evaluation runs, and logging properly will consume ~60% of your hours. This is the same ratio as professional robotics, which is exactly why competitions are good training.

## Staying current in 2026

The volume problem is real: arXiv `cs.RO` alone gets tens of new papers every day, and the robot learning explosion pushed a lot of relevant work into `cs.LG` and `cs.CV` too. Reading everything is impossible. Strategies that work:

1. **Follow the conference cycle, not the firehose.** CoRL, RSS, ICRA, IROS deadlines and acceptance lists act as quality filters. Skim accepted-paper lists twice a year instead of arXiv daily. Our [conferences and journals](../career-paths-and-research-opportunities/conferences-and-journals.md) page has the full calendar and venue tier list.
2. **Workshops over main proceedings.** The state of the art shows up in ICRA/RSS/CoRL workshops 6-12 months before it shows up anywhere archival. Workshop pages are free to browse.
3. **Follow ~10 labs, not 1000 papers.** Pick the groups whose problems match yours and watch their project pages. For me that list changes yearly; right now it's heavy on manipulation and learned navigation groups.
4. **Let newsletters do the triage.** Weekly Robotics plus one venue skim per quarter covers ~90% of what a practicing engineer needs. The remaining 10% you'll hear about from colleagues anyway, because genuinely important results travel fast.
5. **Reproduce one paper a quarter.** Reading is not understanding. Cloning a repo, fighting its dependencies, and running it on your own data teaches you more about a subfield's actual maturity than fifty abstracts.

For alerts that don't require willpower:

* **Google Scholar alerts** on 3-5 specific researchers whose work you build on. Low volume, high relevance.
* **GitHub release watching** on the packages in your production stack (Nav2, your SLAM package, your driver stack). A breaking release you learn about from CI failure is a bad Monday.
* **The robotics-worldwide mailing list** for CFPs and deadline reminders if you publish.

The trap to avoid: confusing *awareness* with *competence*. Knowing every VLA release of the last six months is worth less than having trained one policy end to end on your own robot. Pick your inputs so that at least half your "staying current" time is spent running code, not reading about it.

## Where to go next

* [Conferences and Journals](../career-paths-and-research-opportunities/conferences-and-journals.md) - the full venue list and submission calendar behind the "conference cycle" strategy above.
* [Career in Robotics](../career-paths-and-research-opportunities/career-in-robotics.md) - how these resources map onto actually getting hired.
* [BARN Challenge](../authors-projects/barn-challenge.md) - a concrete account of entering one of the competitions listed here, solo.
* [Imitation Learning](../robot-learning/imitation-learning.md) - the hands-on starting point if the LeRobot community pulled you in.
