# Tasketo

### A python special To-Do-List app with cool design!

I learnd basics of Tkinter libs in Python to make the UI and ***With help from AI in the front end***. Besides that I did make the backend and how the app saves your tasks as JSON file so you can reach them after closing the app alone,

<img width="895" height="712" alt="image" src="https://github.com/user-attachments/assets/921643c7-35b2-453d-a96a-80b8e29a61f0" />

## What it actually does

* **Add tasks** with a category, a priority level, and an optional due date
* **Check them off** and watch a little confetti burst fly out — genuinely satisfying, not gonna apologize for it
* **Search and filter** — All / Today / Starred / Active / Completed, plus a live search bar
* **Sort** by starred items, priority, due date, or newest-first
* **Star tasks** to keep important items at the top
* **Add custom categories** on the fly with the "+ Cat" button
* **Clear completed tasks** with one click
* **Edit anything** by double-clicking a task
* **Undo a delete** with Ctrl+Z if you're trigger-happy with the trash icon
* **Overdue tasks** quietly turn red so you can't pretend you didn't see them
* **5 accent colors** (Indigo, Pink, Emerald, Amber, Sky) — idk why I added this (:
* **Light and dark mode** — there's a moon/sun icon in the corner, click it
* **Everything autosaves** to `tasketo_data.json`, so closing the app doesn't nuke your list

## Getting it running

You need Python 3. That's it. Tkinter comes bundled with most Python installs already, so there's a good chance you don't need to install anything at all.

```
python3 tasketo.py
```

If that throws an error about `tkinter` not being found, it means your Python install stripped it out (this is pretty common btw). Fix it with:

```
# Windows
pip install tk
# Linux
sudo apt install python3-tk

# macOS (via Homebrew Python)
brew install python-tk
```

# want your own version ?

### just edit the files and run `build.py`, you will find your version in `dist` folder !

Alternatively, you can download the [Release](https://github.com/timodev96-alt/Tasketo/releases/download/Tasketo/Tasketo.exe) and simply double-click the file to start using it immediately!
