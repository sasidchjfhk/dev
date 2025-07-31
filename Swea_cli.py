

import os
import sys
import json
import requests
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.prompt import Prompt

class DevikaCLI:
    def __init__(self):
        self.base_url = "http://localhost:1337"  
        self.console = Console()
        self.current_project = None
        self.headers = {"Content-Type": "application/json"}
        
    def generate_response(self, user_input: str) -> str:
        """Generate a response based on user input"""
        user_input = user_input.lower()
        
        if any(greeting in user_input for greeting in ["hi", "hello", "hey"]):
            return "Hello! I'm Devika, your AI assistant. How can I help you today?"
            
        elif "how are you" in user_input:
            return "I'm just a program, so I don't have feelings, but I'm here and ready to help you with your coding tasks!"
            
        elif any(cmd in user_input for cmd in ["create", "make", "build"]) and "react" in user_input:
            return "I can help you create a React application. Please use the 'react' command followed by your project name.\nExample: `react my-app`"
            
        elif "help" in user_input:
            return "I can help you with various tasks. Here are some things you can ask:\n- Create a React app\n- Build a website\n- Help with JavaScript/Python/other programming languages\n- Debug code\n- Explain programming concepts"
            
        # Default response
        return f"I'm Devika, your AI assistant. You asked: {user_input}\n\nI can help you with coding tasks. Try asking me to create a React app or help with a specific programming problem."
        
    def print_header(self):
        """Print the Devika CLI header"""
        header = """
  ____            _     _           
 |  _ \  ___  ___(_) __| | ___  ___ 
 | | | |/ _ \/ __| |/ _` |/ _ \/ __|
 | |_| |  __/ (__| | (_| | (_) \__ \
 |____/ \___|\___|_|\__,_|\___/|___/
                                    
AI Software Engineer - CLI Interface
        """
        self.console.print(Panel(header, style="bold blue"))
        self.console.print("Type 'help' to see available commands\n")

    def make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the Devika backend"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            else:
                response = requests.post(url, json=data, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")
            return {"error": str(e)}

    def list_projects(self):
        """List all projects"""
        data = self.make_request("/api/data")
        if "projects" in data:
            self.console.print("\n[bold]Your Projects:[/bold]")
            for idx, project in enumerate(data["projects"], 1):
                self.console.print(f"  {idx}. {project}")
        else:
            self.console.print("[yellow]No projects found.[/yellow]")

    def create_project(self, project_name: str):
        """Create a new project via Devika API"""
        if not project_name or not project_name.strip():
            self.console.print("[red]Please provide a valid project name. Usage: new <project_name>[/red]")
            return
        endpoint = "/api/create-project"
        data = {"project_name": project_name}
        resp = self.make_request(endpoint, method="POST", data=data)
        if "message" in resp:
            self.console.print(f"[green]{resp['message']}[/green]")
            self.current_project = project_name
        else:
            self.console.print(f"[red]Failed to create project: {resp.get('error', 'Unknown error')}[/red]")

    def create_react_app(self, project_name: str):
        """Create a new React application"""
        self.console.print(f"[green]Creating React application:[/green] {project_name}")
        
        try:
            # Make sure npx is available
            result = os.system("npx --version")
            if result != 0:
                self.console.print("[red]Error: npx is not installed. Please install Node.js and npm first.[/red]")
                return False
                
            # Create React app
            cmd = f"npx create-react-app {project_name}"
            self.console.print(f"[blue]Running:[/blue] {cmd}")
            
            with self.console.status("Creating React application...", spinner="dots"):
                result = os.system(cmd)
                
            if result == 0:
                self.console.print(f"[green]Successfully created React app:[/green] {project_name}")
                self.console.print(f"\nTo start the development server, run:")
                self.console.print(f"  cd {project_name}")
                self.console.print("  npm start\n")
                return True
            else:
                self.console.print("[red]Failed to create React application.[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            return False
    
    def agent_chat(self, message: str, base_model="gpt-4", search_engine="google"):
        """Send a message to the agent and display the response"""
        if not self.current_project:
            self.console.print("[yellow]No project selected. Please create or select a project first.[/yellow]")
            return
        endpoint = "/api/messages"
        data = {
            "project_name": self.current_project,
            "message": message,
            "base_model": base_model,
            "search_engine": search_engine
        }
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            task = progress.add_task("Devika is thinking...", total=None)
            resp = self.make_request(endpoint, method="POST", data=data)
        # Debug: print full backend response for troubleshooting
        self.console.print(f"[dim]Full backend response: {resp}[/dim]")
        if "messages" in resp:
            for msg in resp["messages"]:
                who = "Devika" if msg.get("from_devika") else "You"
                self.console.print(f"[bold]{who}:[/bold] {msg['message']}")
        else:
            self.console.print(f"[red]No response from Devika. {resp.get('error', '')}[/red]")

    def chat(self, message: Optional[str] = None, model="gpt-4o-mini", engine="google"):
        """Start a chat session with Devika (real backend interaction)"""
        if not self.current_project:
            self.console.print("[yellow]No project selected. Please create or select a project first.[/yellow]")
            return
        if not message:
            self.console.print("\n[bold]Chat with Devika (type 'exit' to quit)[/bold]")
        while True:
            try:
                if not message:
                    user_input = Prompt.ask("\nYou").strip()
                    if user_input.lower() == 'exit':
                        break
                else:
                    user_input = message
                    message = None  # Clear the message after first use
                if user_input.lower().startswith("create a react app"):
                    project_name = user_input[17:].strip() or self.current_project
                    self.create_react_app(project_name)
                    continue
                self.agent_chat(user_input, base_model=model, search_engine=engine)
                if message:
                    break
            except KeyboardInterrupt:
                self.console.print("\n[red]Chat session ended.[/red]")
                break

    def status(self):
        """Check backend status, available models, and search engines"""
        data = self.make_request("/api/data")
        if "models" in data and "search_engines" in data:
            self.console.print("[bold green]Backend is running![/bold green]")
            self.console.print("[bold]Available Models:[/bold]")
            for model in data["models"]:
                self.console.print(f"  - {model}")
            self.console.print("[bold]Available Search Engines:[/bold]")
            for engine in data["search_engines"]:
                self.console.print(f"  - {engine}")
        else:
            self.console.print("[red]Backend is not responding or missing info.[/red]")
            if "error" in data:
                self.console.print(f"[red]{data['error']}[/red]")

    def run(self):
        """Run the CLI"""
        self.print_header()
        default_model = "gpt-4o-mini"
        default_engine = "google"
        while True:
            try:
                if self.current_project:
                    prompt = f"devika:{self.current_project}> "
                else:
                    prompt = "devika> "
                
                command = Prompt.ask(prompt).strip().split()
                if not command:
                    continue
                    
                cmd = command[0].lower()
                args = command[1:]
                
                if cmd in ["exit", "quit"]:
                    self.console.print("[green]Goodbye![/green]")
                    break
                elif cmd == "help":
                    self.show_help()
                elif cmd == "status":
                    self.status()
                elif cmd == "projects":
                    self.list_projects()
                elif cmd == "new":
                    project_name = " ".join(args) if args else None
                    self.create_project(project_name)
                elif cmd == "chat":
                    # Usage: chat [--model MODEL] [--engine ENGINE] <message>
                    model = default_model
                    engine = default_engine
                    message_args = []
                    i = 0
                    while i < len(args):
                        if args[i] == "--model" and i+1 < len(args):
                            model = args[i+1]
                            i += 2
                        elif args[i] == "--engine" and i+1 < len(args):
                            engine = args[i+1]
                            i += 2
                        else:
                            message_args.append(args[i])
                            i += 1
                    message = " ".join(message_args) if message_args else None
                    self.chat(message, model, engine)
                elif cmd == "react":
                    project_name = " ".join(args) if args else self.current_project
                    if not project_name:
                        self.console.print("[red]Please specify a project name or create a project first.[/red]")
                    else:
                        self.create_react_app(project_name)
                elif cmd == "clear":
                    os.system("clear" if os.name == "posix" else "cls")
                else:
                    self.console.print("[yellow]Unknown command. Type 'help' for available commands.[/yellow]")
            except KeyboardInterrupt:
                self.console.print("\n[red]Use 'exit' or 'quit' to exit.[/red]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
    
    def show_help(self):
        """Show help message"""
        help_text = """
[bold]Available Commands:[/bold]

  projects                 List all projects
  new [project_name]       Create a new project
  chat [message]           Start a chat with Devika (or send a single message)
  react [project_name]    Create a new React application
  status                  Check backend status, available models, and search engines
  clear                   Clear the screen
  help                    Show this help message
  exit | quit             Exit the CLI

[bold]Chat Command Options:[/bold]
  chat [--model MODEL] [--engine ENGINE] <message>

[bold]Examples:[/bold]
  new my_project          Create a new project named 'my_project'
  chat                    Start an interactive chat session
  chat --model gpt-4 "Hello, Devika!"   Send a single message to Devika using GPT-4
  chat --engine google "How do I build a web app?"   Use Google as the search engine
"""
        self.console.print(help_text)

if __name__ == "__main__":
    try:
        cli = DevikaCLI()
        cli.run()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
