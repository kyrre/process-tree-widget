# A process tree visualization widget

This project contains the source code for a interactive process tree visualization widget. 
Please refer to [this blog
post](https://www.linkedin.com/posts/anja-olsen-5a2643b9_visualizing-process-trees-with-marimo-and-activity-7301269407752683522-0kp5/?utm_source=share&utm_medium=member_desktop&rcm=ACoAADhsJbUBGCHud9Vayji0NXbs1mZ7yzVyygM)
for all the details.


![Process Tree Visualization](image.png)


## Instructions

For the Python dependencies:

1. `uv venv --python 3.12`
2. `uv sync`
3. `source .venv/bin/activate`

In order to build the JavaScript side of the project:

1. `npm install`
2. `npm run dev`

Now you can use `marimo` to play around with the included demo notebook:

`marimo edit example.py`


In order to build the package simply: `uv build`

and for the WebAssembly notebook:

1. `uv build`
2. `cp dist/* public`
3. `marimo export html-wasm wasm_example.py -o output_dir --mode edit`
