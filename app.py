import gradio as gr

def greet(name, intensity):
    """
    A function that takes in a name and an intensity level, and returns a greeting.
    """
    return "Hello " + name + "!" * intensity

demo = gr.Interface(fn=greet, inputs=["text", "slider"], outputs="text")

demo.launch()
