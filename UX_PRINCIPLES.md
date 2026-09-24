# BOT Print Suite UX Principles

The product must make a complex print-production process feel simple to
people who may be using business software for the first time.

## Default experience

- Show only the information needed for the current decision.
- Put uncommon technical fields in a clearly named, collapsed optional section.
- Give every unfamiliar field short helping text and a realistic example.
- Prefer sensible defaults and values copied from the previous document.
- Never ask the user to enter a value the system can calculate or retrieve.

## Navigation and actions

- Each screen should make the current status and the next action obvious.
- Use one visually dominant primary action; secondary actions must not compete with it.
- Use the words spoken in the print shop, not framework or accounting terminology.
- Explain what will happen before an action creates production, stock, or financial documents.
- Preserve ERPNext's standard documents and workflows underneath the simplified experience.

## Readability and accessibility

- Use readable text sizes, generous spacing, and large click targets.
- Never communicate meaning through colour alone; include text and/or an icon.
- Use short sentences and direct instructions instead of dense explanatory paragraphs.
- Provide English and Arabic labels where a shared shop-floor screen benefits from both.
- Error messages must say what is wrong and what the user should do next.

## Progressive complexity

- Customer-facing forms collect the minimum needed to begin the conversation.
- Sales and estimating screens reveal technical detail only when that role needs it.
- Production screens emphasize sequence, quantities, approval state, and the next physical task.
- Advanced controls remain available to experienced users without being placed in the main path.

## Verification standard

For every important workflow, test whether a first-time user can answer these questions without
training:

1. Where am I?
2. What is the current status?
3. What do I need to do now?
4. What will happen after I do it?
5. If something is blocked, how do I fix it?
