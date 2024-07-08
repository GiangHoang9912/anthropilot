import os
import time
import asyncio
import threading
import fnmatch
from anthropilot import Anthropilot
from asyncio import Queue
from flask_cors import CORS
from messages import Message
from dotenv import load_dotenv
from flask import Flask, request, Response, stream_with_context, jsonify

load_dotenv()
app = Flask(__name__)
CORS(app)

code_extensions = ('.ts', '.js', '.rs', '.tsx', '.vue', '.php', '.json', '.py')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        print(data)

        model = data.get("model", "")
        workspace = data.get("workspace", "")
        is_stream = data.get("is_stream", False)
        open_ai_key = data.get("open_ai_key", "")
        anthropic_api_key = data.get("anthropic_api_key", "")
        message = data.get("message", "")
        anthropilot = Anthropilot(
            open_ai_key=open_ai_key,
            anthropic_key=anthropic_api_key,
            model_name=model
        )
        build_template = Message()
        workspace_name = workspace.split("/")[-1]
        workspace_db = "data/faiss_db/" + workspace_name

        if os.path.exists(workspace_db) == False:
            code_files_content = []
            for root, dirs, files in os.walk(workspace):
                for file in files:
                    if file.lower().endswith(code_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            code_files_content.append({
                                'file_name': file_path,
                                'content': content
                            })
                        except Exception as e:
                            print(f"Error reading file {file_path}: {e}")

            raw_text = ""
            for code_file in code_files_content:
                raw_text += code_file['content']

            anthropilot.create_vector_db_from_text(raw_text=raw_text, vector_db_path=workspace_db)
        template = build_template.get_message('template')
        prompt = anthropilot.create_prompt(template=template)
        db = anthropilot.read_vectors_db(workspace_db)
        if is_stream:
            queue = Queue()
            def run_coroutine_in_thread(q: Queue):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    stream = anthropilot.stream_data(message, prompt, db, q)
                    loop.run_until_complete(stream)
                finally:
                    loop.close()
            task = threading.Thread(
                target=run_coroutine_in_thread,
                args=(queue,)
            )
            task.start()
            async def generate(q: Queue):
                while True:
                    if not q.empty():
                        data = await q.get()
                        print(f"data: {data}\n\n")
                        yield f"data: {data}\n\n"

                        if (data == "END"):
                            q = Queue()
                            break
                    time.sleep(0.1)
            def sync_generate(q: Queue):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                gen = generate(q)
                while True:
                    try:
                        yield loop.run_until_complete(gen.__anext__())
                    except StopAsyncIteration:
                        break

            return Response(stream_with_context(sync_generate(q=queue)), mimetype='text/event-stream')
        else:
            response = anthropilot.chat(message, prompt, db)
            return jsonify(response)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/', methods=['GET'])
def health():
    return jsonify({'message': 'Server is running'}), 200

app.run(host='0.0.0.0', debug=True, port=os.getenv('APP_PORT'))