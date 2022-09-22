# The object types of OpenGL

OpenGL has a lot of object types: Texture, FBO, VBO, shader, etc. Most of them can be bound,
bindings are part of the enormous OpenGL state machine, and it's not obvious which functions use
which objects.

This is a (to my knowledge (it's quite limited)) comprehensive list of which bound objects, and
other global variables, each function uses. Explicit parameters, such as glCompileShader taking a
shader object, are not mentioned.

Rare and deprecated functions and operations, such as glBegin, glGenSamplers and glSecondaryColor,
are not mentioned either; I've only included ones I understand and can find practical usecases for.

Finally, this is not a tutorial. It is a complement to one, for people like me who can't wrap our
heads around implicit parameters and other global state. I will not explain anything in any detail.

Bindable object            | Create and bind with                      | Description                                             | Used when drawing?<br>(As input unless otherwise specified)
-------------------------- | --------------------                      | -----------                                             | ------------------
Shader program             | glCreateProgram<br>glUseProgram           | Programmable vertex and fragment rendering instructions | Yes, the bound one
Texture                    | glGenTextures<br>glBindTexture            | N-dimensional array of pixel color data                 | As input if bound in a texture unit,<br>as output (and input for blending) if pointed to by FBO
Texture unit               | (automatic)<br>glActiveTexture            | As far as shaders know, you can bind 16 textures at once| Yes, if used by shader
Vertex array object (VAO)  | glGenVertexArrays<br>glBindVertexArray    | Vertex shader inputs                                    | Yes, the bound one
Vertex buffer (VBO)        | glGenBuffers<br>glBindBuffer(&#8203;GL_ARRAY_BUFFER)              | The actual data backing a VAO   | If pointed to by bound VAO
Element buffer object (EBO)|glGenBuffers<br>glBindBuffer(&#8203;GL_ELEMENT_&#8203;ARRAY_BUFFER)|Vertex indices, for deduplication| If using glDrawElements (uses the one in bound VAO)
Framebuffer object (FBO)   | glGenFramebuffers<br>glBindFramebuffer    | Which texture to render to                              | Yes, the bound one
Renderbuffer object (RBO)  | glGenRenderbuffers<br>glBindRenderbuffer  | A texture, but for non-color data, like depth/stencil   | As both input and output, if pointed to by bound FBO, and if enabled by glDepthFunc/glStencilFunc/etc

Other global variables<br>(not part of bindable state) | Set with | Used when drawing?
---------------------- | --------     | ------------------
The monitor            | your hands   | As output, if current framebuffer is the default (zero)
Viewport               | glViewport   | If current framebuffer is the default (zero), I think?
Scissor                | glScissor    | Yes
Clear color            | glClearColor | No (unless you consider glClear drawing)
Depth function         | glDepthFunc  | Yes
Stencil function       | glStencilFunc| Yes
Error flag | glGetError, and every single other function | No

Function | Non-argument inputs and outputs
-------- | -------------------------------
glEnable  | Various parameters, used only when drawing
glDisable | Various parameters, used only when drawing
glClear      | Clear color (if GL_COLOR_BUFFER_BIT), scissor, things pointed to by FBO
glClearColor | Clear color (used by glClear)
glViewport   | Viewport, used when drawing
glScissor    | Scissor, used when drawing
glDepthFunc   | Depth function
glStencilFunc | Stencil function
glGenVertexArrays | Nothing.
glBindVertexArray | VAO
glGenBuffers | Nothing.
glBindBuffer | VBO; if binding GL_ELEMENT_ARRAY_BUFFER, also affects VAO
glBufferData | VBO
glVertexAttribPointer      | VAO, VBO (current VBO is now pointed to by VAO)
glEnableVertexAttribArray  | VAO
glDisableVertexAttribArray | VAO
glCreateShader  | Nothing, the shader functions all tell which shader/program to use.
glShaderSource  | Nothing.
glCompileShader | Nothing.
glDetachShader  | Nothing.
glDeleteShader  | Nothing.
glCreateProgram | Nothing.
glAttachShader  | Nothing.
glLinkProgram   | Nothing.
glUseProgram    | Shader program
glGetUniformLocation | Nothing
glUniform*           | I think uniforms are part of the shader program?
glGenTextures    | Nothing.
glBindTexture    | Texture
glTexImage*      | Texture
glTexSubImage*   | Texture
glTexParameter*  | Texture
glGenerateMipmap | Texture
glActiveTexture  | Texture unit (also changes current texture)
glGenFramebuffers        | Nothing.
glBindFramebuffer        | FBO
glDeleteFramebuffers     | Nothing.
glCheckFramebufferStatus | FBO
glFramebufferTexture2D   | FBO
glGenRenderbuffers        | RBO
glBindRenderbuffer        | RBO
glRenderbufferStorage     | RBO
glFramebufferRenderbuffer | FBO (also takes an RBO argument)
glDrawArrays   | See 'Used when drawing?' columns
glDrawElements | See 'Used when drawing?' columns
