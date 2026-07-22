# Tasketo

### A Python To-Do app that's actually fun to use.

I recently picked up the basics of Tkinter to build the UI - with a little help from AI to get the styling looking sharp. I handled the backend logic entirely on my own, including the JSON data-saving system so your tasks stick around after you close the app.

<img width="895" height="712" alt="image" src="https://github.com/user-attachments/assets/921643c7-35b2-453d-a96a-80b8e29a61f0" />

## How Does it work

* **Add tasks** with categories, priority levels, and due dates
* **Confetti check-offs** because checking items off should feel rewarding
* **Filters & search** (All, Today, Starred, Active, Completed, + live search)
* **Flexaible sorting** by stars, priority, due date, or newest
* **Star important tasks** to pin them up top
* **Custom categories** on the fly via the "+ Cat" button
* **Bulk clear** completed tasks instantly
* **Double-click to edit** any existing task
* **Undo deletes** with `Ctrl+Z`
* **Overdue highlights** in red
* **Theme customization** with 5 accent colors and a light/dark mode toggle
* **Auto-saves** locally to `tasketo_data.json`

## Getting it running

You just need Python 3 installed. Tkinter usually comes pre-bundled with standard Python installations, meaning you probably don't need any extra setup.

```bash
python3 tasketo.py

```

If you hit an error saying `tkinter` isn't found (which happens occasionally depending on how Python was installed), you can grab it with:

```bash
# Windows
pip install tk

# Linux
sudo apt install python3-tk

# macOS (via Homebrew Python)
brew install python-tk

```

# Want your own version?

### Just edit the files and run `build.py`. Your freshly built app will be waiting in the `dist` folder!

Alternatively, you can just grab the ready-to-use executable from the [Releases](https://github.com/timodev96-alt/Tasketo/releases/download/Tasketo/Tasketo.exe) page and double-click to launch it instantly.
