import pygame
import sys
from TopPanel import TopPanel
from GamePanel1 import GamePanel1
from RulePanel import RulePanel
from LosePanel import LosePanel

class MainFrame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((750, 500))
        pygame.display.set_caption("Python版 ゲーム")
        self.clock = pygame.time.Clock()
        
        # 各パネルを作成し、ディクショナリに登録。各パネルを作成する際に screen と MainFrame 自身（self）を渡すことで、パネル内から panelChange() を呼べるようにする。
        self.panels = {
            "toppanel": TopPanel(self.screen, self),
            "gamepanel1": GamePanel1(self.screen, self),
            "rulepanel": RulePanel(self.screen, self),
            "losepanel": LosePanel(self.screen, self)
        }
        # 初期表示パネルをトップパネルに設定
        self.current_panel = "toppanel"
    
    def panelChange(self, panel_name):
        # 登録されているパネル名が渡されたら、current_panel を変更
        if panel_name in self.panels:
            self.current_panel = panel_name
            print("Panel changed to:", panel_name)
            # ゲームパネルへ切り替えるときに初期化をする
            if panel_name == "gamepanel":  
                self.panels["gamepanel"] = GamePanel1(self.screen, self)
    
    # MainFrame の挙動管理
    def run(self):
        running = True
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    # 現在のパネルにイベント処理を委譲
                    self.panels[self.current_panel].handle_event(event)
                    self.panels[self.current_panel].update(event)
            # 現在のパネルの描画
            self.panels[self.current_panel].draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    MainFrame().run()
