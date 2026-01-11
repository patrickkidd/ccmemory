From: https://x.com/akoratana/status/2006177902333714939

1/ Since @JayaGup10 and I wrote about context graphs, the response has been huge...but I've also noticed a few misconceptions worth addressing.

The tldr: context graphs aren't a graph database or structured memory. They require a fundamentally different approach to schema and representation.
This matters because I'm seeing teams reach for familiar tools (Neo4j, vector stores, knowledge graphs) and wonder why their agents aren't getting smarter. The primitives are wrong.

*A few things I want to clarify:*

2/ "Ontology" is an overloaded term. We need to be more precise.

There are prescribed ontologies (rule engines, workflows, governance layers). Palantir built a $50B company on this: a defined layer mapping enterprise data to objects and relationships. You define the schema. You enforce it. It works when you know the structure upfront.

The next $50B company will be built on learned ontologies. Structure that emerges from how work actually happens, not how you designed it to happen. This is important because there’s so much implicit knowledge in decision making that we don’t even realize in the moment, and agents are meant to replicate our judgement!

3/ Enterprise AI has to navigate both. We have lots of priors for prescribed ontologies. We have almost no infrastructure for learning, representing, and updating the implicit ones.

The implicit relationships (which entities get touched together, what co-occurs in decision chains) is the gap. And it's why memory isn't going to solve the problem.

Memory assumes you know what to store and how to retrieve it. But the most valuable context is structure you didn't know existed until agents discovered it through use.

4/ Another misconception: "decision traces are just trajectory logs."

That's like saying embeddings are just keyword indexes. Technically adjacent, conceptually wrong.

Remember when embeddings looked like alien technology? A probabilistic way to represent similarity that made the "solved" problem of fuzzy search look prehistoric. People asked "why do I need this when I have elasticsearch?"

5/ We're at a similar inflection point for structural learning.

Trajectory logs store what happened. Decision traces (done right) learn why it happened. Which entities mattered. What patterns recur. How reasoning flows through organizational state space.

The difference: logs are append-only records. Decision traces are training data for organizational world models. The schema isn't something you define upfront. It emerges from the walks.

6/ What I'm excited about for 2026:
Small, tuned models evaluating agent trajectories to bootstrap context graphs. Purpose-built models that understand decision structure. This is where I see a lot of value from 
@thinkymachines
 
@arizeai
 
@DSPyOSS
  and others.

RL feedback loops for training models that actually learn decision dynamics, not just token prediction. The signal moves from "did you generate good text" to "did the decision work."

7/ Also: simulation infrastructure becoming productizable.

The articles talked about context graphs as "world models for organizational physics." Imagine asking "what breaks if we deploy this Friday?" and getting a real answer from inference over learned system behavior.

It requires having accumulated enough decision traces to model how your systems actually behave

8/ We're at the beginning of something big. The infrastructure for organizational intelligence doesn't exist yet, which means we get to build it.

Huge thanks to everyone who engaged with the original pieces. The conversations have been incredible and have sharpened my thinking on all of this.

If you're building in this space, context graphs, decision infrastructure, agent evaluation, simulation, I want to talk. The best ideas are going to come from the people in the trenches actually making this work.
2026 is going to be fun. 

Let's go.