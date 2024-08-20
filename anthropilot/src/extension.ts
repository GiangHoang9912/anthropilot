// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { Anthropilot } from './anthropilot';
import markdownit from 'markdown-it';

const config = vscode.workspace.getConfiguration('anthropilot');

const OPENAI_API_KEY = config.get<string>('open_ai_key') || "";
const ANTHROPIC_API_KEY = config.get<string>('anthropic_api_key') || "";
const MODEL = config.get<string>('model') || "claude-3-sonnet-20240229";
const API_BASE_URL = config.get<string>('api_base_url') || "http://127.0.0.1:5000/chat";


if (!OPENAI_API_KEY && !ANTHROPIC_API_KEY) {
	vscode.window.showErrorMessage('Please set the OpenAI and Anthropic API keys in the settings');
}

const anthropilot = new Anthropilot({
	open_ai_key: OPENAI_API_KEY,
	anthropic_api_key: ANTHROPIC_API_KEY,
	model: MODEL,
	api_base_url: API_BASE_URL
});
const markdown = markdownit();

// get workspace path
const workspace = vscode.workspace.workspaceFolders;
const workspacePath = workspace ? workspace[0].uri.fsPath : "";

function displayResultsInPanel(resultData: string) {
	const panel = vscode.window.createWebviewPanel(
		'markdownPanel',
		'anthropilot\'s Results',
		vscode.ViewColumn.One,
		{}
	);
	const htmlContent = markdown.render(resultData);
	panel.webview.html = htmlContent;
}

async function askAnthropilotToAnalyzeCode(resolve: any) {
	const editor = vscode.window.activeTextEditor;
	if (editor) {
		const text = editor.document.getText(editor.selection);
		const fileExtension = editor.document.fileName.split('.').pop();
		if (fileExtension) {
			const prompt = "Analyze the " + fileExtension + " code and identify any issues and coding standard not followed in the given code . Provide response in md format```" + text + "```";
			const response = await anthropilot.invoke(prompt, workspacePath);
			displayResultsInPanel(response);
			resolve();
		}
	}
}

async function WriteCodeByAnthropilot() {
	const editor = vscode.window.activeTextEditor;
	if (editor) {
		const selection = editor.selection;
		const newPosition = selection.active.with(selection.end.line + 1);

		const text = editor.document.getText(editor.selection);

		const fileExtension = editor.document.fileName.split('.').pop();
		const res = await anthropilot.invoke(text + ", Provide response as code in " + fileExtension + ". Just code, do not give any additional text", workspacePath);

		// Thay vì chèn trực tiếp, tạo một CompletionItem
		const completionItem = new vscode.CompletionItem(res.replace(/```/g, ''));
		completionItem.insertText = new vscode.SnippetString('\n' + res.replace(/```/g, '') + '\n');
		completionItem.range = new vscode.Range(newPosition, newPosition);

		// Đăng ký provider cho completion
		const provider = vscode.languages.registerCompletionItemProvider(
			{ scheme: 'file', language: fileExtension },
			{
				provideCompletionItems(document, position) {
					if (position.isEqual(newPosition)) {
						return [completionItem];
					}
				}
			},
			'\t' // Trigger suggestion on Tab key
		);

		// Đảm bảo hủy đăng ký provider sau một khoảng thời gian
		setTimeout(() => provider.dispose(), 10000); // Hủy sau 10 giây
	}
}

async function analyzeFile(currentFile: any) {
	const fileExtension = currentFile.fileName.split('.').pop();
	const prompt = "Analyze the " + fileExtension + " code and identify any issues and coding standard not followed in the given code . Provide response in md format```" + currentFile.text + "```";
	const response = await anthropilot.invoke(prompt, workspacePath);
	displayResultsInPanel(response);
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated

	// this code runs whenever your click 'Create Gist' from the context menu in your browser.
	const disposable = vscode.commands.registerCommand(
		"anthropilot.createGist",
		function () {
			// The code you place here will be executed every time your command is executed
			// Display a message box to the user
			vscode.window.showInformationMessage("Hello World from Anthropilot!");
		}
	);

	const command = vscode.commands.registerCommand("uploadCurrentFile.analyze", async (currentFile, selectedFiles) => {
		if (selectedFiles.length) {
			vscode.window.showInformationMessage('Multiple files cannot be analyzed at once by Mei!');
		} else {
			analyzeFile(currentFile);
		}
	});

	const writeCode = vscode.commands.registerCommand('anthropilot.write_code', function () {
		WriteCodeByAnthropilot();
	});

	const analyzeCode = vscode.commands.registerCommand('anthropilot.analyze_code', function () {
		vscode.window.withProgress({
			location: vscode.ProgressLocation.Notification,
			title: 'Analyzing',
			cancellable: false
		}, () => {
			return new Promise(resolve => {

				askAnthropilotToAnalyzeCode(resolve);
			});
		});

	});

	context.subscriptions.push(disposable);
	context.subscriptions.push(writeCode);
	context.subscriptions.push(analyzeCode);
	context.subscriptions.push(command);
}

export function deactivate() { }
