import pygame
import sys

# カスタムイベント（タイマー用）
TIMER_EVENT = pygame.USEREVENT + 1

class GamePanel2:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # 自機の画像読み込みと初期設定
        # ufo003.png を読み込み、サイズは 50x38 にスケーリング
        self.jiki_ima = pygame.image.load("images/ufo003.png").convert_alpha()
        self.jiki_ima_scaled = pygame.transform.scale(self.jiki_ima, (50, 38))
        self.jiki_w = 50
        self.jiki_h = 38
        self.jiki_y = 10
        
        # ビームの初期設定
        self.jiki_beam_x = 30
        self.jiki_beam_y = 30
        self.jiki_beam_flg = 0
        
        # 「TopPanelに移動」ボタンの矩形とテキスト
        self.btn_rect = pygame.Rect(150, 50, 200, 40)
        self.btn_text = "Return TopPanel"
        self.font_btn = pygame.font.SysFont("Arial", 20)
        
        # 80msごとにタイマーイベントを発生させる
        pygame.time.set_timer(TIMER_EVENT, 80)
    
    def handle_key(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.jiki_y -= 10
            elif event.key == pygame.K_DOWN:
                self.jiki_y += 10
            elif event.key == pygame.K_z and self.jiki_beam_flg == 0:
                # Z キーでビーム発射
                self.jiki_beam_x = 40
                self.jiki_beam_y = self.jiki_y + 15
                self.jiki_beam_flg = 1
    
    def handle_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos  # マウスクリック位置を取得
            if self.btn_rect.collidepoint(pos):
                print("TopPanelに移動 ボタンがクリックされました")
                # ここに画面遷移処理などを追加可能
    
    def update(self, event):
        # タイマーイベント（80msごと）の処理
        if event.type == TIMER_EVENT:
            if self.jiki_beam_flg == 1:
                self.jiki_beam_x += 100
            if self.jiki_beam_x > self.width + 100:
                self.jiki_beam_flg = 0
    
    def draw(self):
        # 背景を黒で塗りつぶす
        self.screen.fill((0, 0, 0))
        
        # 自機（ufo）の描画：左側は固定 x=40、y座標は self.jiki_y
        self.screen.blit(self.jiki_ima_scaled, (40, self.jiki_y))
        
        # ビームが発射中なら、黄色の線を描画する
        if self.jiki_beam_flg == 1:
            # 開始座標 (80, self.jiki_beam_y) から、終点 (self.jiki_beam_x+100, self.jiki_beam_y)
            pygame.draw.line(self.screen, (255, 255, 0), (80, self.jiki_beam_y), (self.jiki_beam_x + 100, self.jiki_beam_y), 3)
        
        # ボタンの描画（灰色の矩形＋テキストを中央配置）
        pygame.draw.rect(self.screen, (200, 200, 200), self.btn_rect)
        btn_text_surf = self.font_btn.render(self.btn_text, True, (0, 0, 0))
        btn_text_rect = btn_text_surf.get_rect(center=self.btn_rect.center)
        self.screen.blit(btn_text_surf, btn_text_rect)

"""
def main():
    pygame.init()
    screen = pygame.display.set_mode((750, 500))
    pygame.display.set_caption("Python版 GamePanel2")
    clock = pygame.time.Clock()
    
    panel = GamePanel2(screen)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            panel.handle_key(event)
            panel.handle_mouse(event)
            panel.update(event)
        panel.draw()
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
"""