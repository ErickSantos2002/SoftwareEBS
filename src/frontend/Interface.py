import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize

# Adiciona o diretório "src" ao sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, "src")
sys.path.append(src_dir)

# Cores e Estilos
COR_CINZA = "#969595"  # Cinza
COR_AZUL = "#0072B7"   # Azul
COR_PRETO = "#0C0C0E"  # Preto
COR_BRANCA = "#FFFFFF"  # Branco


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EBS-010 Interface")
        self.setGeometry(100, 100, 1200, 800)

        # Configurações de estilo geral
        self.setStyleSheet(f"background-color: {COR_CINZA};")

        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra superior
        self.create_top_bar(main_layout)

        # Área principal
        self.main_area = QWidget()
        self.main_area.setStyleSheet(f"background-color: {COR_CINZA};")
        main_layout.addWidget(self.main_area)

    def create_top_bar(self, layout):
        """Cria a barra superior com gradiente e insere os botões e a logo."""
        # Widget da barra superior com gradiente
        top_bar = QWidget()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet("""
            background: qlineargradient(
                spread:pad,
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #0072B7, stop:1 #FFFFFF
            );
        """)

        # Layout interno do top_bar
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0)
        top_layout.setSpacing(20)

        # Widget para os botões e a logo (sem gradiente)
        inner_widget = QWidget()
        inner_layout = QHBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(20)

        # Adiciona os botões e a logo
        self.add_buttons_with_icons(inner_layout)

        # Adiciona o inner_widget ao top_layout
        top_layout.addWidget(inner_widget)

        # Adiciona a barra ao layout principal
        layout.addWidget(top_bar)

    def add_buttons_with_icons(self, layout):
        """Adiciona os botões com ícones e a logo na barra superior."""
        ICONES = {
            "Registros": "assets/Registros.png",
            "Testes": "assets/Testes.png",
            "Resultados": "assets/Resultados.png",
            "Configurações": "assets/Configuracoes.png",
            "Informações": "assets/Informacoes.png",
        }

        # Itera sobre os botões
        for nome, icone in ICONES.items():
            botao = QPushButton()
            botao.setText(nome)
            botao.setIcon(QIcon(icone))
            botao.setIconSize(QSize(40, 40))  # Ajuste do tamanho do ícone
            botao.setFont(QFont("Arial", 12, QFont.Bold))
            botao.setStyleSheet(f"""
                QPushButton {{
                    border: none;  /* Sem borda */
                    background: transparent;  /* Sem fundo */
                    color: {COR_PRETO};  /* Texto na cor preta */
                }}
                QPushButton:hover {{
                    color: {COR_AZUL};  /* Texto azul ao passar o mouse */
                }}
            """)
            botao.clicked.connect(self.criar_conexao(nome))  # Usa a função auxiliar para conectar cada botão
            layout.addWidget(botao)

        # Adiciona a logo como um botão clicável
        logo_path = "assets/Logo.png"
        logo_button = QPushButton()
        logo_button.setIcon(QIcon(logo_path))
        logo_button.setIconSize(QSize(80, 40))  # Tamanho ajustado da logo
        logo_button.setStyleSheet("border: none; background: transparent;")
        logo_button.clicked.connect(self.resetar_tela_principal)  # Ação ao clicar na logo
        layout.addWidget(logo_button)

    def criar_conexao(self, nome):
        """Cria uma conexão para o botão com o nome especificado."""
        def on_click():
            if nome == "Registros":
                self.abrir_modulo("Registros_Tela")
            elif nome == "Testes":
                self.abrir_modulo("Testes.py")
            elif nome == "Resultados":
                self.abrir_modulo("Resultados.py")
            elif nome == "Configurações":
                self.abrir_modulo("Configuracoes.py")
            elif nome == "Informações":
                self.abrir_modulo("Informacoes.py")
        return on_click

    def abrir_modulo(self, modulo):
        """Carrega o módulo especificado na área principal."""
        # Redefine o fundo da área principal
        self.main_area.setStyleSheet(f"background-color: {COR_CINZA};")
        
        # Verifica se a área principal já tem um layout e remove-o
        layout_atual = self.main_area.layout()
        if layout_atual is not None:
            while layout_atual.count():
                item = layout_atual.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            layout_atual.deleteLater()
        
        # Define um novo layout para a área principal
        novo_layout = QVBoxLayout()
        self.main_area.setLayout(novo_layout)

        # Carrega o módulo especificado
        if modulo == "Registros_Tela":
            from frontend.Registros_Tela import RegistrosTela
            tela_registros = RegistrosTela(self)
            novo_layout.addWidget(tela_registros)
        else:
            # Mensagem ou tela padrão para módulos não implementados
            label = QLabel(f"Módulo {modulo} não implementado.")
            label.setAlignment(Qt.AlignCenter)
            novo_layout.addWidget(label)

    def carregar_registros(self, layout):
        """Carrega a tela de Registros_Tela na área principal."""
        from frontend.Registros_Tela import RegistrosTela  # Importa o widget da tela de registros
        
        # Limpa widgets anteriores da área principal
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Adiciona a tela de registros à área principal
        registros_tela = RegistrosTela(parent=self)
        layout.addWidget(registros_tela)

    def carregar_testes(self, layout):
        """Carrega o módulo de Testes na área principal."""
        label = QLabel("Módulo: Testes")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(label)

    def carregar_resultados(self, layout):
        """Carrega o módulo de Resultados na área principal."""
        label = QLabel("Módulo: Resultados")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(label)

    def carregar_configuracoes(self, layout):
        """Carrega o módulo de Configurações na área principal."""
        label = QLabel("Módulo: Configurações")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(label)

    def carregar_informacoes(self, layout):
        """Carrega o módulo de Informações na área principal."""
        label = QLabel("Módulo: Informações")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(label)

    def resetar_tela_principal(self):
        """Reseta a tela inicial cinza."""
        self.main_area.setStyleSheet(f"background-color: {COR_CINZA};")
        
        # Verifica se a área principal já tem um layout e remove-o
        layout_atual = self.main_area.layout()
        if layout_atual is not None:
            while layout_atual.count():
                item = layout_atual.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            layout_atual.deleteLater()

        # Define o layout inicial
        inicial_layout = QVBoxLayout()
        self.main_area.setLayout(inicial_layout)

        label = QLabel("Área Principal")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        inicial_layout.addWidget(label)


    # Criação da área central
        self.central_area = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_area.setLayout(self.central_layout)
        self.setCentralWidget(self.central_area)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
