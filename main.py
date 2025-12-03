import http.server
import socketserver
import json
import urllib.request
import urllib.error
import sys
import os
import webbrowser

from duckduckgo_search import DDGS

PORT = 8000
OLLAMA_URL = "http://localhost:11434/api/generate"

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                user_idea = data.get('idea', '')
                model = data.get('model', 'gemma3:4b')
                
                # 1. Search for references (Multi-Query)
                print(f"Searching for references for: {user_idea}")
                references_text = "\n\nGEFUNDENE REFERENZEN (Nutze diese als Inspiration):\n"
                
                queries = [
                    f"{user_idea} official website brand",      # Find the brand (e.g. Louis Vuitton)
                    f"{user_idea} github repository source code", # Find code
                    f"{user_idea} ui ux design dribbble behance" # Find design
                ]
                
                found_links = set()
                
                try:
                    with DDGS() as ddgs:
                        for q in queries:
                            print(f"  Query: {q}")
                            results = list(ddgs.text(q, max_results=4))
                            for res in results:
                                if res['href'] not in found_links:
                                    references_text += f"- [{res['title']}]({res['href']}): {res['body'][:200]}...\n"
                                    found_links.add(res['href'])
                                    
                    # Add Hardcoded Best Practices & User Repo
                    references_text += "\nZUSÄTZLICHE EXPERTEN-REFERENZEN:\n"
                    references_text += "- [User Repository](https://github.com/graf-julian08/Website-Generator): Spezifische User-Vorgaben.\n"
                    references_text += "- [Vercel Commerce](https://github.com/vercel/commerce): High-Performance E-Commerce Template.\n"
                    references_text += "- [MedusaJS](https://github.com/medusajs/medusa): Open Source Headless Commerce Engine.\n"
                    references_text += "- [WooCommerce](https://github.com/woocommerce/woocommerce): Best Practice für PHP-basierte Shops.\n"
                                    
                except Exception as e:
                    print(f"Search failed: {e}")
                    references_text += "\n(Suche fehlgeschlagen, nutze allgemeines Wissen.)"

                system_prompt = f"""
                Du bist ein Senior Software Architect und World-Class Prompt Engineer.
                Deine Aufgabe: Erstelle basierend auf der Idee "{user_idea}" 6 ABSOLUTE MEISTERWERK-PROMPTS für ein LLM.
                
                {references_text}
                
                **TECH STACK VORGABE:**
                - Frontend: HTML5, Modern CSS3 (Variables, Flexbox, Grid), Vanilla JavaScript (ES6+).
                - Backend: PHP 8+ (Modern, Objektorientiert), MySQL/MariaDB.
                - Architektur: MVC (Model-View-Controller) oder saubere Trennung von Logik und Design.
                
                **ANFORDERUNGEN AN DIE PROMPTS:**
                - **EXTREME DETAILTIEFE:** Beschreibe nicht nur "was" gemacht werden soll, sondern "WIE". Nenne Dateinamen, Funktionen, Klassen, Variablen.
                - **WORKFLOWS:** Beschreibe Schritt-für-Schritt-Anleitungen für die Umsetzung.
                - **PROFESSIONALITÄT:** Der Code muss Production-Ready, sicher und skalierbar sein.
                
                **STRUKTUR DER 6 PROMPTS:**
                
                |||PROMPT_START|||
                **PROMPT 1: DESIGN & KONZEPT (The Vision)**
                - Detaillierte Beschreibung des visuellen Stils (Farbcodes, Typografie, Abstände).
                - UX/UI Flows: Wie bewegt sich der User durch den Shop?
                - Mockup-Beschreibung für: Homepage, Produktseite, Warenkorb, Checkout.
                - Referenz-Integration: Nutze die gefundenen Links für konkrete Design-Anweisungen.
                
                |||PROMPT_START|||
                **PROMPT 2: FRONTEND ARCHITEKTUR (The Skeleton)**
                - Exakte Dateistruktur (Ordner, Dateien).
                - HTML5 Boilerplate mit Semantic Tags.
                - JavaScript Modul-Struktur (kein Spaghetti-Code!).
                - Einbindung von Assets (Fonts, Icons).
                
                |||PROMPT_START|||
                **PROMPT 3: BACKEND LOGIK & DATENBANK (The Brain)**
                - Vollständiges Datenbank-Schema (SQL Tabellen, Relationen, Indizes).
                - PHP-Klassenstruktur (z.B. `Database.php`, `Product.php`, `Cart.php`).
                - Session-Management, Login/Register Logik, Warenkorb-Logik (CRUD).
                - Sicherheitsmaßnahmen im Code (Prepared Statements, Input Validation).
                
                |||PROMPT_START|||
                **PROMPT 4: STYLING & ANIMATION (The Soul)**
                - CSS Architektur (z.B. BEM Naming Convention oder Utility Classes).
                - Responsive Breakpoints (Mobile, Tablet, Desktop).
                - Keyframe-Animationen, Transitions, Hover-Effekte (Luxus-Feeling).
                - Muss 1:1 das Design aus Prompt 1 umsetzen.
                
                |||PROMPT_START|||
                **PROMPT 5: CMS & ADMIN DASHBOARD (The Control)**
                - Dashboard-Design und Funktionen (Produkte verwalten, Bestellungen einsehen).
                - Analytics-Ansicht (Charts, Graphen).
                - Admin-Login und Rechteverwaltung.
                - Stil: So hochwertig wie das Frontend (Louis Vuitton Style Admin).
                
                |||PROMPT_START|||
                **PROMPT 6: DEPLOYMENT, SECURITY & OPTIMIZATION (The Shield)**
                - Checkliste gegen Cyber-Angriffe (XSS, CSRF, SQLi).
                - Performance-Optimierung (Caching, Minification, Image Compression).
                - SEO-Strategie (Meta-Tags, Schema.org Structured Data).
                - Deployment-Anleitung (Apache/Nginx Config, .htaccess).
                
                REGELN:
                1. KEINE Einleitung, KEIN "Hier ist der Plan". Starte direkt mit `|||PROMPT_START|||`.
                2. Sei so präzise, dass ein Junior-Entwickler den Code blind schreiben könnte.
                """
                
                ollama_req_body = {
                    "model": model,
                    "prompt": system_prompt,
                    "stream": True
                }
                
                req = urllib.request.Request(
                    OLLAMA_URL,
                    data=json.dumps(ollama_req_body).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                
                try:
                    with urllib.request.urlopen(req) as response:
                        for line in response:
                            if line:
                                decoded_line = line.decode('utf-8')
                                try:
                                    json_resp = json.loads(decoded_line)
                                    if 'response' in json_resp:
                                        chunk = json_resp['response']
                                        # SSE format: data: <content>\n\n
                                        # We need to escape newlines in the data to be valid SSE
                                        safe_chunk = json.dumps(chunk) # This handles escaping
                                        self.wfile.write(f"data: {safe_chunk}\n\n".encode('utf-8'))
                                        self.wfile.flush()
                                except json.JSONDecodeError:
                                    pass
                                    
                    self.wfile.write(b"event: done\ndata: {}\n\n")
                    self.wfile.flush()
                    
                except urllib.error.URLError as e:
                    err_msg = json.dumps(f"Error connecting to Ollama: {e}")
                    self.wfile.write(f"event: error\ndata: {err_msg}\n\n".encode('utf-8'))
                    
            except Exception as e:
                print(f"Error: {e}")
        else:
            self.send_error(404)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    # Change to directory of script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with ReusableTCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Opening browser...")
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
