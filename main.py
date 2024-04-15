import gradio as gr
import numpy as np

def invert_colors(input_image):
    return 255 - input_image


def sepia_filter(input_image):
    filter = np.array([
        [0.393, 0.769, 0.180],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = input_image.dot(filter.T)
    sepia_img /= sepia_img.max()
    print("Input image:")
    print(input_image)
    print("Sepia image:")
    print(sepia_img)
    print("Input shape:", input_image.shape)
    print("Filter shape:", filter.shape)
    return sepia_img


def do_operation(input_image, operation):
    if operation == "Invert colors":
        return invert_colors(input_image)
    elif operation == "Sepia":
        return sepia_filter(input_image)
    else:
        return input_image


dropdown_menu = gr.Dropdown(
    choices=["Invert colors", "Sepia"], label="Image operation", info="Will add more operations later!"
)

# An interface that uses inputs as input arguments in the function
# fn and returns any number of outputs.
demo = gr.Interface(
    fn=do_operation,
    inputs=[gr.Image(), dropdown_menu],
    outputs=[gr.Image()]
)

# To share using a public link, use share=True.
demo.launch()

