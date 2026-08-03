---
description: How robotics hiring actually works - portfolios, open source, interview prep by role, PhD vs industry, and applying without going insane.
icon: user-tie
---

# Getting Hired

### **Now Go Get One**

[Job Roles](job-roles-in-robotics.md) tells you what the 21 titles mean. [Companies Hiring](companies-hiring-for-robotics.md) tells you who's staffed for them. Neither tells you what to actually do about it. This page is written the way I wish someone had written it for me when I was applying out of IIT Patna.

Two things I will not do here. I will not quote you salary numbers - they go stale within months and vary wildly by geography and company stage, so if you want compensation data go look at aggregators like **levels.fyi** or **Glassdoor** and treat even those skeptically. And I will not invent acceptance rates, "X% of applicants get an interview," or claims about what any specific company's loop looks like this year. Anyone who tells you that with confidence is guessing or violating an NDA. What follows is mechanism, not statistics.

***

### **The Portfolio Is the Resume**

In most software hiring, your resume is a proxy for what you can do. In robotics, you can often just show what you can do, and it beats the proxy every time. A hiring manager who sees a robot actually drive, actually grasp, actually localize - on video, with code behind it - has more signal in ninety seconds than in a page of bullet points.

A portfolio project that actually works has four ingredients:

| Ingredient | What it means | What it isn't |
|---|---|---|
| **Real hardware or a serious simulation** | A physical robot, or a simulator with real physics and real constraints (Gazebo, Isaac Sim, MuJoCo) | A notebook that calls a pretrained model on a static image |
| **A demo video** | Unedited or lightly edited footage of the thing working, ideally also failing informatively | A GIF of the one run that worked, with no context |
| **A README that explains decisions** | Why GICP over ICP, why an EKF over a particle filter, what the failure modes are | A wall of setup instructions and no reasoning |
| **Honest limitations** | "This breaks past 1.5 m/s because the LiDAR deskewing assumes constant velocity" | Silence about the parts that don't work |

That last row is the one people skip and shouldn't. Every reviewer who has shipped anything knows every project has edges. Naming yours signals you understand the system rather than got lucky with a demo run.

This handbook's own [Author's Projects](../authors-projects/authors-projects.md) section is written to that exact template - go read it as a worked example, not because you should copy the projects, but because you should copy the shape: motivation, engineering decisions, a demo artifact, and an honest "what I'd do differently." The [BARN Challenge](../authors-projects/barn-challenge.md) entry in that section is also a good example of a different kind of credential: a public, adversarial benchmark where your score is a number someone else computed, not a claim you're making about yourself. If a benchmark exists in your subfield - BARN for navigation, KITTI or TUM for SLAM, a public leaderboard for your kind of manipulation task - submitting to it is worth more than another private demo, because it can't be dismissed as cherry-picked.

{% hint style="info" %}
**My bias, stated plainly.** I think a mediocre GPA with one project that actually runs on real hardware beats a great GPA with none. I can't prove that with statistics and I wouldn't trust anyone who claims to have them. It's a pattern I've seen hold in every hiring conversation I've been part of, on either side of the table.
{% endhint %}

***

### **Open Source as a Career Path, Not a Hobby**

Robotics has an unusually good open-source-to-job pipeline, for structural reasons that don't apply to most of software:

- **The ecosystem is small.** There are maybe a few hundred people who meaningfully maintain [ROS 2](../ros-2/ros-2.md) core, Nav2, MoveIt, and the handful of tools everyone uses. They know each other. A maintainer vouching for you carries weight a cold resume can't.
- **Maintainers are visible and reachable.** Unlike a large corporate codebase, you can DM the person who reviewed your PR. Conference hallway conversations at ROSCon turn into "oh, you're the person who fixed the costmap layer bug" - that's a warmer intro than any recruiter screen.
- **A merged PR is verifiable evidence, not a claim.** Anyone can put "contributed to ROS 2" on a resume. Not everyone can point to a commit hash. The difference is checkable in thirty seconds.

Good targets to start with: **Nav2**, **MoveIt**, ROS 2 core packages, **PlotJuggler**, **Foxglove**/**Lichtblick**, and **LeRobot** (Hugging Face's robot learning library, now central to a lot of imitation-learning work - see [Robot Learning](../robot-learning/robot-learning.md)). I maintain a small presence in Nav2, PlotJuggler, and Lichtblick myself, and the on-ramp was the same every time:

1. **Reproduce a bug first, before writing any code.** Most "good first issue" labels are exactly that, but the highest-leverage thing you can do as a stranger is confirm someone else's bug report with your own environment and post the repro steps. It costs you an hour and it's immediately useful.
2. **Fix docs before you fix code.** Docs PRs get reviewed faster, teach you the codebase's conventions, and get your name in the contributor list while you're still learning where the bodies are buried.
3. **Then take a `good-first-issue`.** By this point you've read enough of the codebase's style and CI to not waste a maintainer's review cycles.
4. **Stay on for the unglamorous stuff.** Triaging issues, updating a deprecated API call, keeping a package building on a new ROS distro. This is what actually gets you recognized, more than a single flashy feature PR.

None of this is a fast path. It compounds over months, same as everything else that's actually worth having on a resume.

***

### **Interview Preparation, by Role**

Robotics interviews test things generic SWE interviews mostly don't, because the failure modes are different. A backend service that drops a request retries. A robot that drops a message can drive into a wall.

| Role family | What actually gets tested | Study this |
|---|---|---|
| **SLAM / Perception** | Coordinate frames and transforms, probability and estimation (why a Kalman filter is the thing it is, not just how to call one), point cloud registration | [SLAM & State Estimation](../slam-and-state-estimation/slam-and-state-estimation.md), especially [Sensor Fusion](../slam-and-state-estimation/sensor-fusion.md) and [Filter SLAM](../slam-and-state-estimation/filter-slam.md) |
| **Motion Planning / Nav2** | Costmaps, behavior trees, planner vs. controller separation, why a plan that's valid at t=0 can be invalid at t=1 | [Nav2 Deep Dive](../ros-2/nav2-deep-dive.md) |
| **Manipulation / MoveIt** | Kinematics, collision checking, grasp planning tradeoffs | [MoveIt 2](../ros-2/moveit2.md) |
| **Embedded / Firmware** | C++ without a heap you trust, real-time constraints, why you can't just `malloc` in a control loop | [Embedded Systems](../embedded-systems-for-robotics/embedded-systems.md), [RTOS](../embedded-systems-for-robotics/rtos.md) |
| **Robot Learning / VLA** | Imitation vs. RL tradeoffs, why more data doesn't always help, sim-to-real gap | [Robot Learning](../robot-learning/robot-learning.md), [Sim-to-Real](../robot-learning/sim-to-real.md) |
| **ROS 2 / Systems** | QoS mismatches, DDS discovery failures, composition vs. separate processes | [DDS & QoS](../ros-2/dds-qos.md), [Lifecycle & Composition](../ros-2/lifecycle-and-composition.md) |

A handful of questions show up across almost every role family, in some form:

- **"Your node is dropping messages - what do you check?"** This is a systems-debugging question disguised as a trivia question. The answer they want isn't a single fact, it's a search order: QoS mismatch (reliability, depth, durability) between publisher and subscriber, callback group starvation, executor overload, network/DDS discovery issues, then finally "is the publisher actually publishing." If you jump straight to "increase queue depth" without checking QoS first, that's a tell.
- **"Tell me about a time the robot broke and how you found the root cause."** Every working robotics engineer has a story like this, because hardware always breaks. What they're evaluating is whether you have a method - hypothesis, minimal test, verify, repeat - or whether you just changed things until it stopped happening. If your last debugging story ends in "and then it just started working," that's not a strong answer.
- **"Walk me through the frames involved in getting a LiDAR point into the map."** This is coordinate-transform literacy in disguise. If you can't rattle off sensor frame to base_link to odom to map, with a word on why odom-to-map is the one that jumps, that's a gap worth closing before the interview, not during it.
- **"Why would you choose an EKF over a particle filter here, or vice versa?"** Not a request for a textbook definition. They want to know if you understand the tradeoff: Gaussian unimodal assumption and speed versus multimodal robustness and compute cost, and whether you've actually had to make that call under a hardware constraint.

If a live coding round shows up, it looks a lot more like generic SWE (data structures, sometimes a small C++ or Python task) than a robotics-specific problem. Don't neglect that half of your prep just because the domain-specific questions are more interesting to study.

***

### **How to Actually Apply**

Robotics is a small field. The people building humanoids, AMRs, and SLAM stacks largely know of each other's work even across competing companies, because the community that goes to the same three or four conferences is not that large. That changes the math on how you should spend your effort.

| Channel | Effort | Why it works or doesn't |
|---|---|---|
| **Cold application** | Low effort, low signal | Fine as a baseline, but you're one PDF in a queue with nothing to differentiate you before a human looks |
| **Referral** | Medium effort | Someone inside vouches, which gets you past the first filter - but a referral from someone who's never seen your work is barely better than cold |
| **Conference contact (ROSCon, ICRA, IROS)** | High effort, high payoff | See [Conferences and Journals](conferences-and-journals.md) for the calendar. A five-minute hallway conversation where you show someone your robot on your phone is worth more than most cover letters, because it's memorable and it's proof, not a claim |
| **Open-source visibility** | Compounds over time | A maintainer or a fellow contributor who's reviewed your PRs already has a read on how you think, before you ever apply anywhere |

If you can only invest in one non-obvious channel, I'd pick showing up to a robotics conference over polishing a cover letter. It's a stronger use of the same hours.

One more thing worth saying about cold applications specifically, since most people still send a lot of them: match your resume's language to the exact role family, not a generic "robotics engineer" label. [Job Roles in Robotics](job-roles-in-robotics.md) lists the titles and scope that recruiters and applicant-tracking systems are actually pattern-matching against - if you did SLAM work, say SLAM, not "autonomy." Vague titling is a self-inflicted wound at the resume-screening stage, before a human ever reads the substance.

***

### **Internships and Early Career**

Research internships (a university lab, a national lab, a BRAIn-Lab-style academic group) and industry internships (a startup or established robotics company) select for different things and prepare you for different things.

| | Research internship | Industry internship |
|---|---|---|
| **What you're handed** | A paper to reproduce, or an open question from a professor or postdoc | An existing, often messy codebase with a deadline attached |
| **Feedback cadence** | Weekly check-in, long stretches of your own judgment in between | Code review on every PR, daily standups |
| **Deliverable** | A result, a manuscript-in-preparation, sometimes a publication | A shipped feature or fix that survives integration |
| **What it signals to a future employer** | You can work with ambiguity and read primary literature | You can ship inside someone else's system under a deadline |
| **How to convert it** | Turn the result into a workshop paper or a public write-up before you leave | Take the task nobody wants and finish it cleanly before you leave |

Whichever kind you land, converting an internship into a full-time offer is mostly about making yourself annoying to not hire: finish what you start, write it up so the next person doesn't have to re-derive what you learned, and make sure your mentor or manager can describe in one sentence what you actually did. "Fixed the sensor fusion node's timing bug" is a sentence someone can repeat in a hiring meeting. "Helped with various tasks" is not.

***

### **PhD or Industry**

I'll try to be honest rather than persuasive here, because I think this question gets more preachy advice than it deserves.

**What a PhD buys you in robotics specifically:**

- Access to research-scientist roles at foundation-model labs and research-heavy companies that are structurally hard to reach otherwise.
- A publication record, which is its own credential in a field where conferences like ICRA and IROS (see [Conferences and Journals](conferences-and-journals.md)) function as a large part of the hiring signal for research roles.
- Years of forced depth on one narrow problem, which is genuinely different from years of breadth shipping features.

**What it costs:**

- Multiple years at a stipend, which is an opportunity cost against multiple years of industry experience and career progression - be honest with yourself about which one you value more, because there's no objectively correct answer here.
- Time is not fungible: an idea that would take a strong industry team a quarter can take a PhD a year, because you're also the one debugging your own tooling.

**Where it's genuinely required versus merely common:** research-scientist titles at DeepMind-style labs, most tenure-track academic positions, and a real fraction of foundation-model robotics roles do have a hard PhD requirement. Most SLAM, perception, motion-planning, and ROS 2 engineering roles across the companies in [Companies Hiring](companies-hiring-for-robotics.md) do not - a strong portfolio and relevant experience gets you in the door. When in doubt on a specific posting, "required" versus "preferred" in the job description is usually literally true; take it at face value.

I did not do a PhD before shipping production SLAM and Nav2 work, so take my view as one data point, not a verdict on the decision. If you're weighing it, [Leading Institutes](leading-institutes.md) is the place in this handbook to go look at what specific labs actually work on before you commit years to one of them.

***

### **Remote Work, Visas, and Relocation**

Be honest about this one: robotics is unusually hardware-bound, and that makes it a worse field than most of software for fully remote work. You mostly cannot debug a LiDAR mount, a wiring harness, or a real-time control loop from a laptop in a different city. A meaningful chunk of roles - anything touching hardware bring-up, sensor integration, or field testing - expect you on-site or at least on-site often. Software-heavy roles (simulation, some perception and learning work, some ROS 2 tooling) have more remote flexibility, but "more" is relative to a low baseline, not to software engineering generally.

The practical result is that relocation is often just part of the deal, not an edge case. The current hubs worth knowing about, all drawn from the [Companies Hiring](companies-hiring-for-robotics.md) directory:

| Hub | What's concentrated there | Example companies |
|---|---|---|
| **SF Bay Area, USA** | Humanoids, robotaxis, foundation models | Figure AI, Physical Intelligence, Zoox, Waymo |
| **Boston, USA** | Legged robots, warehouse robotics | Boston Dynamics, Symbotic, Locus Robotics |
| **Pittsburgh, USA** | Trucking autonomy, robot foundation models (CMU-adjacent) | Aurora Innovation, Skild AI |
| **Austin, USA** | Humanoids, EV/robotics crossover | Apptronik, Tesla Optimus |
| **Bangalore, India** | AMRs, sensor fusion, vision-guided manipulation (where I'm based) | Ati Motors, CynLr, Addverb R\&D |
| **Shenzhen / Hangzhou, China** | Humanoids, consumer and industrial robots at aggressive price points | Unitree, UBTech, Booster Robotics |
| **London / Cambridge, UK** | AV foundation models, surgical robotics | Wayve, CMR Surgical |
| **Odense, Denmark** | Intralogistics AMRs | Mobile Industrial Robots (MiR) |

If a role that matters to you is in one of these, plan for the move being part of the offer, not a footnote.

On visas: I'll stay general here on purpose, because visa eligibility depends on your nationality, the hiring country's specific programs, and rules that change - none of which I'm qualified to advise on and none of which I'll guess at. What's durably true is that sponsorship is a real cost and a real risk for a company, so it narrows your pool of realistic employers, and it's worth asking directly and early in a process rather than discovering it after an offer. Treat anything else you read on this topic, including here, as a starting point for asking a qualified immigration professional, not as an answer.

***

### **The Short Version**

If you read nothing else on this page: build something real, put it somewhere public, show it to people at the two or three conferences where robotics people actually gather, and be honest about what it doesn't do yet. Everything else on this page is detail underneath that one sentence.
