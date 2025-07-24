import os
import sys

def main():
    # Diese Variablen kannst du als Umgebungsvariablen setzen oder direkt anpassen
    input_filename = "BraTS20_Training_036_t1_resample.nii.gz"
    input_path = os.path.join(os.path.sep, "input", input_filename )
    output_path = os.path.join(os.path.sep, "output" )

    # Prüfen ob Input existiert
    if not os.path.exists(input_path):
        print(f"Input file {input_path} does not exist!")
        sys.exit(1)

    # --- Beispiel: Aufruf des SynthSeg-CLI-Skripts aus Python heraus ---
    cmd = (
        f"python SynthSeg/scripts/commands/SynthSeg_predict.py"
        f" --i {input_path}"
        f" --o {output_path}"
        f" --cpu"
        f" --threads 6"
        f" --parc"
        f" --resample {output_path}"
    )
    print(f"Running SynthSeg: {cmd}")
    exitcode = os.system(cmd)
    if exitcode != 0:
        print("SynthSeg failed!")
        sys.exit(1)

    print(f"Segmentation finished. Output at: {output_path}")

if __name__ == "__main__":
    main()