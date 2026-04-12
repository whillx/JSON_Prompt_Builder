# JSON Prompt Builder
A simple GUI text editor to create or edit JSON-style prompts for AI image or video generation.

# Functions
- GUI interface that visualizes the JSON prompt as a tree structure.
- Fully dynamic schema: users can build any JSON structure from scratch. A default template is provided as a starting point, which users can freely modify or delete.
- "+" button on any key-value pair adds a new sibling key-value pair at the same level.
- "-" button on any key-value pair removes it.
- A single field can hold multiple comma-separated values (e.g., `"Style": "Photorealistic, Cinematic"`).
- Users can create, edit, save, and load JSON files.

# Tech Specs
- Written in Python with Tkinter (stdlib only, no external dependencies).
- Portable: runs with just a standard Python installation, no pip install needed.
- Source code organized for readability and easy modification.

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