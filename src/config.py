"""
Configuration for the static content of your GitHub profile.
Use curly braces {} as placeholders for dynamic GitHub stats.
"""

PROFILE_DATA = [
    # --- HEADER ---
    {
        "type": "header",
        "text": "adrian@mazur",
    },
    {
        "type": "text",
        "text": "Hi there! I’m a part-time student at WSEI (University of Information Technology and Management) in Cracow and an AI/ML developer at Archman.",
    },
    {"type": "spacer", "height": 15},
    # --- TOOLS ---
    {
        "type": "text",
        "text": "Tools",
    },
    {
        "type": "group",
        "items": [
            ("Tools.IDE", "Visual Studio Code, Visual Studio"),
            ("Tools.VersionControl", "Git, GitUI"),
            ("Tools.Infrastructure", "Hetzner Cloud, Azure, Docker"),
            ("Tools.Management", "Planka"),
        ],
    },
    {"type": "spacer", "height": 15},
    # --- TECHNOLOGIES ---
    {
        "type": "text",
        "text": "Technologies",
    },
    {
        "type": "group",
        "items": [
            ("Languages.Human", "Polish (Native), English"),
            ("Languages.Core", "Python, C#"),
        ],
    },
    {"type": "spacer", "height": 15},
    # --- HOBBIES ---
    {
        "type": "text",
        "text": "Hobbies",
    },
    {
        "type": "group",
        "items": [
            ("Hobbies.GameDevelopment", "Godot Engine, C#"),
            ("Hobbies.AI", "NLP, ML, Neural Networks"),
            ("Hobbies.Gaming", "PC, Board Games, Chess (chess.com/member/adisonowy)"),
        ],
    },
    {"type": "spacer", "height": 15},
    # --- CONTACT ---
    {
        "type": "header",
        "text": "- Contact ",
    },
    {
        "type": "group",
        "items": [
            ("Contact.Email.Personal", "adrianmazur.dev@proton.me"),
            ("Contact.Email.Work", "adrian.mazur@archman.pl"),
            ("Contact.LinkedIn", "linkedin.com/in/adrianmazur-dev/"),
        ],
    },
    {"type": "spacer", "height": 15},
    # --- GITHUB STATS ---
    {
        "type": "header",
        "text": "- GitHub Stats ",
    },
    {
        "type": "two_column",
        "rows": [
            [("GitHub.Repos", "{repos} public"), ("GitHub.Stars", "{stars}")],
            [
                ("GitHub.Commits", "{commits}"),
                ("GitHub.Contributions", "{total_contributions}"),
            ],
        ],
    },
    {
        "type": "group",
        "items": [
            ("GitHub.Followers", "{followers}"),
        ],
    },
    {"type": "complex_loc", "label": "Github.LOC"},
]
