# Adding Departments

This is the core feature of bootcamp-company. As you use it, the secretary suggests adding departments.

## Suggestions from the Secretary

When the same task comes up a second time, the secretary proposes a department together with a manual (written procedure). Empty departments are never created.

```
> Research competitors for me
Secretary: Sure, I'll look into it.

(A few days later...)

> Research another competitor
Secretary: This is the second competitor research.
           I'll create a Research department and put today's steps there as a "Competitor research" manual.
           Next time, the Research department will follow it. Shall I create it?

You: Yes, create it

→ .company/research/ is created with one manual in manuals/
```

## Direct Requests

You can also request directly. The secretary first asks for one task to hand over, and that becomes the first manual.

```
> Create a PM department
Secretary: Sure. Tell me one task you want PM to handle first.
           I'll make it PM's first manual.

→ .company/pm/ is created with one manual in manuals/
```

## What Gets Created

When a department is added, the following are auto-generated:

- **Department folder** — `.company/[department]/`
- **Department CLAUDE.md** — Rules and behavior for that department
- **Subfolders** — For file management
- **Templates** — For creating new files

For example, adding a Research department:

```
.company/
├── CLAUDE.md              ← Department list gets updated
├── secretary/
└── research/              ← Newly added
    ├── CLAUDE.md           ← Research rules
    └── topics/             ← Research topic management
```

## Available Departments

| Department | Area |
|-----------|------|
| PM | Project progress, ticket management |
| Research | Market research, competitive analysis, tech research |
| Marketing | Content planning, SNS, campaigns |
| Engineering | Technical docs, design, debugging |
| Finance | Invoices, expenses, revenue management |
| Sales | Client management, proposals |
| Creative | Design briefs, brand management |
| HR | Recruitment, team management |

See the [Departments Reference](/en/reference/departments) for details.
