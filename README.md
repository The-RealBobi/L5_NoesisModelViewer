# Level-5 Engine Noesis Script

This Noesis script allows you to load `.g4md` and `.g4pkm` files used in games created with the Level-5 engine.

## Installation

1. **Download Noesis**: Download Noesis from [here](https://richwhitehouse.com/index.php?content=inc_projects.php&showproject=91).
2. **Install the Script**: Place the Noesis script in 
the `plugins/python` folder inside the Noesis folder.

⚠️ (If you have any other script that supports previewing Level-5 models with texture files, you may have to remove it, since it may conflict on the decryption of the textures when previewing the model) 

## Previewing models

To preview the model with the textures applied, you must have the model, mesh, and texture files in the same folder and have them sharing the **exact same name** (e.g., `c11010060.g4md`, `c11010060.g4pkm`, `c11010060.png`).

⚠️ Not all models work correctly with this script.

### Example folder structure:

```plaintext
/c11010060
    c11010060.g4pkm / c11010060.g4md
    c11010060.g4mg
    c11010060.g4tx
```
## To-do:
- Support model skeletons.
