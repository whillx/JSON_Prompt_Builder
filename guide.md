# JSON Prompt Builder
A simple GUI text editor to create or edit JSON-style prompts for AI image or video generation.

# Functions
- GUI interface that visualizes the JSON prompt as a tree structure.
- Fully dynamic schema: users can build any JSON structure from scratch. A default template is provided as a starting point, which users can freely modify or delete.
- "+" button on any key-value pair adds a new sibling key-value pair at the same level.
- "-" button on any key-value pair removes it.
- A single field can hold multiple comma-separated values (e.g., `"Style": "Photorealistic, Cinematic"`).
- Users can create, edit, save, and load JSON files.
- **Drag-and-drop reordering**: drag items up or down to reorder them among siblings. A blue indicator line shows the drop position.
- **Copy and paste**: right-click any item (string, object, or array) to copy it, then right-click another entry and paste. The copied item is inserted as a sibling — it does not overwrite the selected entry.
- **Value suggestions**: when editing a value whose key matches a suggestion file (e.g. Lens, Shot type, Weather, Time of Day, Medium, Angle), a filterable dropdown appears with suggested values. Typing in the field filters the list. Key matching is case-insensitive.
- Suggestions live in the `Suggestion/` folder as plain `.txt` files — one file per field, one suggested term per line. The filename (without `.txt`) is matched against the key being edited. To add or change suggestions, just edit or drop in a new `.txt` file; no code changes needed. Suggestions are not language-dependent.

# Tech Specs
- Written in Python with Tkinter (stdlib only, no external dependencies).
- Portable: runs with just a standard Python installation, no pip install needed.
- Source code organized for readability and easy modification.

# Adding a New Language
1. Copy `locale/en.json` to `locale/xx.json` and translate all values, including the `"language_name"` key.
2. The language appears automatically in the Language menu — no code changes needed.

# Default Template
The app launches with the following default template, which users can freely edit or delete:

```json
{
	"General": {
		"Style": "Photorealistic",
		"Camera Model": "ARRI ALEXA 35",
		"Camera Angle": "Frontal",
		"Time": "Sunset"
	},
	"Contents": [
		{
			"Type": "People",
			"Description": "An ancient warrior",
			"Position": "Middle of the frame",
			"Gesture": "Standing"
		},
		{
			"Type": "Object",
			"Description": "A tree",
			"Position": "Middle of the frame",
			"Gesture": "Standing"
		}
	]
}
```
