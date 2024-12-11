import sys
import os
from PyQt5.QtWidgets import QApplication
from src.frontend.Interface import MainWindow  # Interface principal

# Determina o caminho base do projeto
BASE_DIR = (
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
)

# Adiciona a pasta "src" ao sistema de caminhos
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Instancia e exibe a janela principal
    main_window = MainWindow()
    main_window.show()

    # Executa o loop principal do aplicativo
    sys.exit(app.exec_())
