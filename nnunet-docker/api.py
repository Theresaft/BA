from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/nnunet_predict/<unique_id>', methods=['GET'])
def run_nnunet_predict(unique_id):
    try:
        print("unique_id: ", unique_id)
        input_dir = f'/app/nnunet/input/{unique_id}'
        output_dir = f'/app/nnunet/output/{unique_id}'
        command = f'nnUNet_predict -i {input_dir} -o {output_dir} -t 1 -m 3d_fullres'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify({'message': 'nnUNet_predict command executed successfully.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e), 'output': e.output.decode('utf-8')}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
