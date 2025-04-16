import pygame
import sys
import random

# カスタムイベントの定義
TIMER_EVENT    = pygame.USEREVENT + 1
HAIKEI1_EVENT  = pygame.USEREVENT + 2
HAIKEI2_EVENT  = pygame.USEREVENT + 3
HAIKEI3_EVENT  = pygame.USEREVENT + 4
HAIKEI4_EVENT  = pygame.USEREVENT + 5
HAIKEI5_EVENT  = pygame.USEREVENT + 6
HAIKEI6_EVENT  = pygame.USEREVENT + 7

class GamePanel1:
    def __init__(self, screen, mainframe):
        self.screen = screen
        self.mainframe = mainframe  # 遷移先としてトップパネルに戻るための参照

        # 用意されてるスクリーンサイズの取得
        self.width, self.height = screen.get_size()
        
        # 画像の読み込み（各ファイルは実行ディレクトリに配置）
        self.haikei_ima1 = pygame.image.load("images/utyuu.png").convert()
        self.haikei_ima2 = pygame.image.load("images/utyuu.png").convert()
        self.haikei_ima3 = pygame.image.load("images/earth2.png").convert()
        self.clear_ima   = pygame.image.load("images/clear.png").convert()
        self.jiki_ima    = pygame.image.load("images/ufo003.png").convert_alpha()  # 自機の画像
        self.teki_ima    = pygame.image.load("images/meteo2.png").convert_alpha()
        self.enemy_ima   = pygame.image.load("images/teki.jpg").convert()

        # タイマーの開始
        pygame.time.set_timer(TIMER_EVENT, 80)
        pygame.time.set_timer(HAIKEI1_EVENT, 70)  # タイマー1スタート
        pygame.time.set_timer(HAIKEI2_EVENT, 0)
        pygame.time.set_timer(HAIKEI3_EVENT, 0)
        pygame.time.set_timer(HAIKEI4_EVENT, 0)
        pygame.time.set_timer(HAIKEI5_EVENT, 0)
        pygame.time.set_timer(HAIKEI6_EVENT, 0)
        
        # 背景用変数
        self.haikei_x1 = 0
        self.haikei_x2 = 0
        self.haikei_width = self.haikei_ima1.get_width()
        self.haikei_height = self.haikei_ima1.get_height()
        self.haikei_flg = 0
        self.earth_width = self.haikei_ima3.get_width()
        self.earth_height = self.haikei_ima3.get_height()
        self.earth_x = 0
        self.small = 1.0
        self.goal_jiki_y = 20  # 初期は自機の y 座標
        
        # ゲームオーバーフラグ
        self.lose = 0
        
        # 自機（jiki）の位置とサイズ
        self.jiki_x = 40
        self.jiki_y = 20
        self.jiki_w = self.jiki_ima.get_width()
        self.jiki_h = self.jiki_ima.get_height()
        self.jiki_beam_x = -100
        self.jiki_beam_y = self.jiki_y + 19
        self.jiki_beam_flg = 0
        
        # 敵（隕石）のビーム・オブジェクト用
        self.n = 5
        self.teki_x = [0] * self.n
        self.teki_y = [0] * self.n
        self.teki_w = self.teki_ima.get_width()
        self.teki_h = self.teki_ima.get_height()
        for i in range(self.n):
            ratio = random.random() * 5
            self.teki_y[i] = i * self.teki_h + 100
            self.teki_x[i] = int(ratio * 200 + self.width)
        self.teki_tama_x = [0] * self.n
        self.teki_tama_y = [0] * self.n
        self.teki_tama_alive = [0] * self.n
        for i in range(self.n):
            ratio = random.random()
            self.teki_tama_y[i] = int(self.height * ratio)
            self.teki_tama_x[i] = self.teki_x[i] + 2 * self.teki_w
            self.teki_tama_alive[i] = 1
        self.teki_tama_w = self.teki_w
        self.teki_tama_h = self.teki_h
        
        # 敵（enemy）の初期化
        self.n_enemy = 40
        self.w_enemy = self.enemy_ima.get_width()
        self.h_enemy = self.enemy_ima.get_height()
        self.x_enemy = [0] * self.n_enemy
        self.y_enemy = [0] * self.n_enemy
        self.vx_enemy = [0] * self.n_enemy
        self.vy_enemy = [0.0] * self.n_enemy
        self.v_random = [0.0] * self.n_enemy
        self.enemy_move_flg = [False] * self.n_enemy
        self.enemy_alive = [1] * self.n_enemy
        self.enemy_last = 0
        for i in range(self.n_enemy):
            self.x_enemy[i] = 750 + int(self.haikei_width * random.random())
            self.y_enemy[i] = int(self.haikei_height * random.random())
            self.vx_enemy[i] = -5
            self.enemy_alive[i] = 1
            self.enemy_move_flg[i] = False
            self.v_random[i] = random.random()
        
        # ボタン（Topパネルへ戻る）の定義
        self.btn_rect = pygame.Rect(100, 390, 200, 40)
        self.btn_visible = False
        self.btn_text = "Return Top"
        self.font_btn = pygame.font.SysFont("Arial", 20)
    
        # 既存の初期化処理
        self.reset()  # 初期化時にリセット処理を呼ぶ


    def reset(self):
        # ① タイマーを初期状態に戻す
        pygame.time.set_timer(HAIKEI1_EVENT, 70)
        pygame.time.set_timer(HAIKEI2_EVENT, 0)
        pygame.time.set_timer(HAIKEI3_EVENT, 0)
        pygame.time.set_timer(HAIKEI4_EVENT, 0)
        pygame.time.set_timer(HAIKEI5_EVENT, 0)
        pygame.time.set_timer(HAIKEI6_EVENT, 0)

        # ② 背景用変数の初期化
        self.haikei_x1 = 0
        self.haikei_x2 = 0
        self.haikei_width = self.haikei_ima1.get_width()
        self.haikei_height = self.haikei_ima1.get_height()
        self.haikei_flg = 0
        self.earth_width = self.haikei_ima3.get_width()
        self.earth_height = self.haikei_ima3.get_height()
        self.earth_x = 0
        self.small = 1.0
        self.goal_jiki_y = 20  # 初期は自機の y 座標

        # ③ 自機の初期化
        self.jiki_x = 40
        self.jiki_y = 20
        self.jiki_beam_flg = 0
        self.jiki_beam_x = -100

        # ④ 背景フラグを「スクロール開始」状態に
        self.haikei_flg = 1
        self.haikei_x1  = 0
        self.haikei_x2  = 0

        # ⑤ 隕石関連
        for i in range(self.n):
            # 生存フラグを立てる
            self.teki_tama_alive[i] = 1
            # Y 座標は画面内のランダム位置
            self.teki_tama_y[i]     = random.randint(0, self.height - self.teki_tama_h)
            # X 座標は画面右端 + α の位置
            # （ここでは隕石幅×2 分だけ右にオフセット）
            self.teki_tama_x[i]     = self.width + self.teki_tama_w * 2

        # ⑥ 敵（enemy）の初期化
        self.n_enemy = 40
        self.w_enemy = self.enemy_ima.get_width()
        self.h_enemy = self.enemy_ima.get_height()
        self.x_enemy = [0] * self.n_enemy
        self.y_enemy = [0] * self.n_enemy
        self.vx_enemy = [0] * self.n_enemy
        self.vy_enemy = [0.0] * self.n_enemy
        self.v_random = [0.0] * self.n_enemy
        self.enemy_move_flg = [False] * self.n_enemy
        self.enemy_alive = [1] * self.n_enemy
        self.enemy_last = 0
        for i in range(self.n_enemy):
            self.x_enemy[i] = 750 + int(self.haikei_width * random.random())
            self.y_enemy[i] = int(self.haikei_height * random.random())
            self.vx_enemy[i] = -5
            self.enemy_alive[i] = 1
            self.enemy_move_flg[i] = False
            self.v_random[i] = random.random()

        # ⑦ フラグの初期化
        self.enemy_last = 0
        self.lose = 0
        self.btn_visible = False
    

    # キーイベントとマウスイベントをまとめる
    def handle_event(self, event):
        # キーイベントなら handle_key() を呼び出す
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            self.handle_key(event)
        # マウスイベントなら handle_mouse() を呼び出す
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.handle_mouse(event)
    
    # キーイベント
    def handle_key(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and self.jiki_y > 0:
                self.jiki_y -= 10
            if event.key == pygame.K_DOWN:
                if self.jiki_y <= self.height - 30:
                    self.jiki_y += 10
                else:
                    self.jiki_y = self.height - 30
            if event.key == pygame.K_z and self.jiki_beam_flg == 0:
                self.jiki_beam_x = 40
                self.jiki_beam_y = self.jiki_y + 15
                self.jiki_beam_flg = 1
            self.goal_jiki_y = self.jiki_y
    
    # マウスイベント
    def handle_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_visible and self.btn_rect.collidepoint(pos):
                print("Topパネル戻る ボタンがクリックされました")
                # ここで画面切替などの処理を追加可能
                self.mainframe.panelChange("toppanel")
    
    def update(self, event):
        # メインタイマー（80ms）
        if event.type == TIMER_EVENT:
            for i in range(self.n):
                if self.teki_tama_x[i] >= -self.teki_w:
                    self.teki_tama_x[i] -= (i+1) * 4
                if self.teki_tama_x[i] < -self.teki_w:
                    ratio = random.random()
                    self.teki_tama_x[i] = self.width
                    self.teki_tama_y[i] = int(self.height * ratio)
                    self.teki_tama_alive[i] = 1
                # クリア状態でなければ当たり判定を実施
                if self.enemy_last == 0:
                    # 自機（jiki）と敵ビームとの当たり判定
                    if (self.jiki_x+25 > self.teki_tama_x[i] and 
                        self.jiki_x+25 < self.teki_tama_x[i] + self.teki_tama_w and
                        self.teki_tama_y[i] < self.jiki_y+19 and
                        self.jiki_y+19 < self.teki_tama_y[i] + self.teki_tama_h and
                        self.teki_tama_alive[i] == 1):
                        self.lose = 1
            
            if self.jiki_beam_flg == 1:
                self.jiki_beam_x += 100
            if self.jiki_beam_x > self.width + 100:
                self.jiki_beam_flg = 0
                self.jiki_beam_x = -200
            if self.jiki_beam_flg == 1:
                for i in range(self.n):
                    if (self.teki_tama_alive[i] == 1 and
                        self.teki_tama_x[i] < self.jiki_beam_x < self.teki_tama_x[i] + self.teki_tama_w and
                        self.teki_tama_y[i] < self.jiki_beam_y < self.teki_tama_y[i] + self.teki_tama_h):
                        self.teki_tama_alive[i] = 0
                        self.jiki_beam_flg = 0
        
        elif event.type == HAIKEI1_EVENT:
            self.haikei_flg = 1
            self.haikei_x1 -= 10
            if self.haikei_x1 <= -self.width * 6:
                pygame.time.set_timer(HAIKEI1_EVENT, 0)  # タイマー1停止
                pygame.time.set_timer(HAIKEI2_EVENT, 70)   # タイマー2開始
                self.haikei_x2 = 0
        elif event.type == HAIKEI2_EVENT:
            for i in range(self.n_enemy):
                if self.x_enemy[i] - 40 < 600:
                    self.enemy_move_flg[i] = True
                if not self.enemy_move_flg[i]:
                    self.x_enemy[i] -= 5
                else:
                    self.x_enemy[i] += self.vx_enemy[i]
                    self.vy_enemy[i] = (self.jiki_y - self.y_enemy[i]) * self.v_random[i] / 20
                    self.y_enemy[i] += int(self.vy_enemy[i])
            for i in range(self.n_enemy):
                if (self.jiki_x+25 > self.x_enemy[i] and 
                    self.jiki_x+25 < self.x_enemy[i] + self.w_enemy and
                    self.jiki_y+19 > self.y_enemy[i] and 
                    self.jiki_y+19 < self.y_enemy[i] + self.h_enemy):
                    self.lose = 1
            self.haikei_flg = 2
            self.haikei_x2 -= 10
            if self.haikei_x2 <= -self.width * 6:
                pygame.time.set_timer(HAIKEI2_EVENT, 0)
                pygame.time.set_timer(HAIKEI3_EVENT, 70)
                self.haikei_x1 = 0
        elif event.type == HAIKEI3_EVENT:
            self.haikei_flg = 2
            self.haikei_x2 -= 10
            if self.haikei_x2 <= -self.width * 6:
                pygame.time.set_timer(HAIKEI3_EVENT, 0)
                pygame.time.set_timer(HAIKEI4_EVENT, 70)
                self.haikei_x1 = 0
        elif event.type == HAIKEI4_EVENT:
            self.haikei_flg = 2
            self.haikei_x2 -= 10
            if self.haikei_x2 <= -self.width * 6:
                pygame.time.set_timer(HAIKEI4_EVENT, 0)
                pygame.time.set_timer(HAIKEI5_EVENT, 70)
                self.haikei_x1 = 0
        elif event.type == HAIKEI5_EVENT:
            self.haikei_flg = 3
            self.earth_x -= 5
            if self.earth_x + self.width <= self.width - self.earth_width:
                pygame.time.set_timer(HAIKEI5_EVENT, 0)
                pygame.time.set_timer(HAIKEI6_EVENT, 70)
            # タイマー5の処理終了後、画面更新は main ループで行う
        elif event.type == HAIKEI6_EVENT:
            self.haikei_flg = 4
            self.jiki_x += 10
            self.small += 0.1
            denom = self.width - self.jiki_x - self.earth_width
            if denom != 0:
                self.goal_jiki_y += (self.height - self.goal_jiki_y - self.earth_height) / denom * 10
            if self.jiki_x + (50 // int(self.small)) >= self.width + self.earth_x:
                pygame.time.set_timer(HAIKEI6_EVENT, 0)
                self.enemy_last = 1

        # 「負け」が確定したら LosePanel へ移行
        if self.lose == 1 and self.enemy_last == 0:
            self.mainframe.panelChange("losepanel")
            return  # 以降の update や draw は不要なので抜ける
        
        
    def draw(self):
        # 背景を黒で塗りつぶし
        self.screen.fill((0, 0, 0))
        if self.lose == 0:
            if self.haikei_flg == 1:
                img = pygame.transform.scale(self.haikei_ima1, (self.width * 5, self.height))
                self.screen.blit(img, (self.haikei_x1 + self.width, 0))
            if self.haikei_flg == 2:
                img = pygame.transform.scale(self.haikei_ima2, (self.width * 5, self.height))
                self.screen.blit(img, (self.haikei_x2 + self.width, 0))
            if self.haikei_flg in [1, 2, 3]:
                img_jiki = pygame.transform.scale(self.jiki_ima, (50, 38))
                self.screen.blit(img_jiki, (self.jiki_x, self.jiki_y))
                if self.jiki_beam_flg == 1:
                    pygame.draw.line(self.screen, (255, 255, 0), (80, self.jiki_beam_y),
                                     (self.jiki_beam_x+100, self.jiki_beam_y), 3)
            if self.haikei_flg in [3, 4]:
                img_earth = pygame.transform.scale(self.haikei_ima3, (100, 100))
                self.screen.blit(img_earth, (self.earth_x + self.width, self.height - self.earth_height))
            if self.enemy_last == 0:
                for i in range(self.n_enemy):
                    if self.enemy_alive[i] == 1:
                        self.screen.blit(self.enemy_ima, (self.x_enemy[i], self.y_enemy[i]))
                for i in range(self.n):
                    if self.teki_tama_alive[i] == 1:
                        self.screen.blit(self.teki_ima, (self.teki_tama_x[i], self.teki_tama_y[i]))
        if self.haikei_flg == 4:
            scale_factor = int(self.small)
            if scale_factor == 0:
                # クリアアニメーション中：自機が地球に迫っていく動きを描画する
                scale_factor = max(1, int(self.small))
            img_jiki2 = pygame.transform.scale(self.jiki_ima, (50 // scale_factor, 38 // scale_factor))
            self.screen.blit(img_jiki2, (self.jiki_x, int(self.goal_jiki_y)))
            if self.enemy_last == 1:
                # 本当のクリア画面
                img_clear = pygame.transform.scale(self.clear_ima, (self.width, self.height))
                self.screen.blit(img_clear, (0, 0))

            # クリア後は必ずボタンを表示
            self.btn_visible = True
            pygame.draw.rect(self.screen, (200, 200, 200), self.btn_rect)
            btn_text_surf = self.font_btn.render(self.btn_text, True, (0, 0, 0))
            btn_text_rect = btn_text_surf.get_rect(center=self.btn_rect.center)
            self.screen.blit(btn_text_surf, btn_text_rect)


# 挙動確認
if __name__ == "__main__":
    # ダミーのメインフレーム（panelChange の挙動を確認するため）
    class DummyMainFrame:
        def panelChange(self, panel_name):
            print("Panel changed to:", panel_name)
    
    pygame.init()
    screen = pygame.display.set_mode((750, 500))
    pygame.display.set_caption("GamePanel1")
    clock = pygame.time.Clock()
    
    # ダミーのメインフレームオブジェクトを作成し、GamePanel1 に渡す
    dummy_mainframe = DummyMainFrame()
    panel = GamePanel1(screen, dummy_mainframe)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                panel.handle_event(event)
                panel.update(event)
        panel.draw()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()