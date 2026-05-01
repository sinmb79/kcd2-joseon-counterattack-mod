(function () {
  "use strict";

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  const menu = document.getElementById("menu");
  const startBtn = document.getElementById("start-btn");
  const W = canvas.width;
  const H = canvas.height;

  const keys = new Set();
  const mouse = { x: W / 2, y: H / 2, down: false };
  let justAttack = false;
  let justInteract = false;
  let justDeploy = false;
  let lastTime = 0;

  const facts = [
    "1592년 4월 14일 부산진성 전투",
    "1592년 4월 15일 동래성 전투",
    "이순신 장군 생존: 전라좌수영 준비 중",
  ];

  const missions = [
    {
      id: "busanjin",
      title: "1장 부산진 급보",
      date: "1592.4.14",
      briefing:
        "부산진이 무너지는 동안 화약과 장계를 챙겨 동래성으로 이어지는 길을 여십시오.",
      objective: "피난민 2명 구출, 장계 확보, 55초 생존",
      duration: 55,
      goal: { rescued: 2, dispatch: true },
      gateHp: 130,
      spawnRate: 2.4,
      enemyLimit: 11,
      crates: [
        { x: 330, y: 150, type: "powder" },
        { x: 330, y: 440, type: "timber" },
        { x: 560, y: 240, type: "grain" },
        { x: 710, y: 420, type: "dispatch" },
      ],
      civilians: [
        { x: 620, y: 120 },
        { x: 700, y: 300 },
        { x: 570, y: 475 },
      ],
      beacon: { x: 120, y: 112 },
    },
    {
      id: "dongnae",
      title: "2장 동래성의 문",
      date: "1592.4.15",
      briefing:
        "동래성 남문이 압박받고 있습니다. 성을 영원히 지키는 것이 아니라 사람과 장부, 봉화를 살리는 것이 목표입니다.",
      objective: "피난민 4명 구출, 봉화 유지, 75초 버티기",
      duration: 75,
      goal: { rescued: 4, beacon: true },
      gateHp: 170,
      spawnRate: 1.9,
      enemyLimit: 16,
      crates: [
        { x: 300, y: 180, type: "powder" },
        { x: 290, y: 410, type: "timber" },
        { x: 420, y: 500, type: "grain" },
        { x: 535, y: 130, type: "powder" },
      ],
      civilians: [
        { x: 650, y: 120 },
        { x: 710, y: 190 },
        { x: 690, y: 360 },
        { x: 630, y: 470 },
        { x: 760, y: 430 },
      ],
      beacon: { x: 132, y: 88 },
    },
    {
      id: "seed",
      title: "3장 반격의 씨앗",
      date: "1592.5",
      briefing:
        "초기 패전 뒤 산길에서 보급 수레를 지키십시오. 장계가 살아 있어야 조선의 다음 반격이 시작됩니다.",
      objective: "보급 수레 방어, 적 16명 격퇴, 80초 생존",
      duration: 80,
      goal: { kills: 16, cart: true },
      gateHp: 0,
      spawnRate: 1.65,
      enemyLimit: 20,
      crates: [
        { x: 260, y: 160, type: "powder" },
        { x: 250, y: 440, type: "timber" },
        { x: 520, y: 500, type: "grain" },
        { x: 610, y: 170, type: "powder" },
      ],
      civilians: [],
      beacon: { x: 128, y: 100 },
      cart: { x: 210, y: 478, hp: 160 },
    },
  ];

  let state = createState();

  function createState(missionIndex = 0) {
    const mission = missions[missionIndex];
    return {
      mode: "menu",
      missionIndex,
      time: 0,
      spawnTimer: 0.9,
      messageTimer: 0,
      message: "전쟁 초기: 장계와 사람을 살리십시오.",
      player: {
        x: 180,
        y: 320,
        r: 13,
        hp: 100,
        speed: 150,
        facingX: 1,
        facingY: 0,
        shootCd: 0,
        hwachaCd: 0,
      },
      resources: { powder: 2, timber: 2, grain: 3, morale: 70 },
      gate: mission.gateHp > 0 ? { x: 158, y: 300, w: 42, h: 160, hp: mission.gateHp, max: mission.gateHp } : null,
      cart: mission.cart ? { ...mission.cart, max: mission.cart.hp } : null,
      beacon: { ...mission.beacon, lit: mission.id !== "dongnae" },
      crates: mission.crates.map((c, i) => ({ ...c, id: `crate-${i}`, taken: false })),
      civilians: mission.civilians.map((c, i) => ({ ...c, id: `civilian-${i}`, rescued: false, panic: 0 })),
      enemies: [],
      projectiles: [],
      particles: [],
      kills: 0,
      dispatch: false,
      rescued: 0,
      result: "",
      errors: [],
    };
  }

  function currentMission() {
    return missions[state.missionIndex];
  }

  function startMission(index = 0) {
    state = createState(index);
    state.mode = "briefing";
    menu.classList.add("hidden");
    render();
  }

  function beginPlay() {
    if (state.mode === "briefing" || state.mode === "success") {
      if (state.mode === "success") {
        const next = state.missionIndex + 1;
        if (next >= missions.length) {
          state.mode = "complete";
          return;
        }
        state = createState(next);
        state.mode = "briefing";
      } else {
        state.mode = "playing";
      }
    } else if (state.mode === "menu") {
      startMission(0);
    }
  }

  function restartMission() {
    const index = state.missionIndex || 0;
    state = createState(index);
    state.mode = "playing";
    menu.classList.add("hidden");
  }

  startBtn.addEventListener("click", () => startMission(0));

  window.addEventListener("keydown", (event) => {
    const key = event.key.toLowerCase();
    if (["arrowup", "arrowdown", "arrowleft", "arrowright", " ", "tab"].includes(key)) {
      event.preventDefault();
    }
    keys.add(key);
    if (key === "enter") beginPlay();
    if (key === " ") justAttack = true;
    if (key === "e") justInteract = true;
    if (key === "q") justDeploy = true;
    if (key === "r") restartMission();
    if (key === "f") toggleFullscreen();
  });

  window.addEventListener("keyup", (event) => {
    keys.delete(event.key.toLowerCase());
  });

  canvas.addEventListener("mousemove", (event) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * W;
    mouse.y = ((event.clientY - rect.top) / rect.height) * H;
  });

  canvas.addEventListener("contextmenu", (event) => event.preventDefault());

  canvas.addEventListener("mousedown", (event) => {
    if (event.button === 2) {
      justDeploy = true;
      return;
    }
    mouse.down = true;
    if (state.mode === "briefing" || state.mode === "success" || state.mode === "complete") beginPlay();
  });

  window.addEventListener("mouseup", () => {
    mouse.down = false;
  });

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.querySelector(".game-frame").requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  function update(dt) {
    if (state.mode !== "playing") {
      return;
    }
    const mission = currentMission();
    state.time += dt;
    state.player.shootCd = Math.max(0, state.player.shootCd - dt);
    state.player.hwachaCd = Math.max(0, state.player.hwachaCd - dt);
    state.messageTimer = Math.max(0, state.messageTimer - dt);

    movePlayer(dt);
    updateCivilians(dt);
    updateEnemies(dt);
    updateProjectiles(dt);
    updateParticles(dt);
    updateSpawning(dt);

    if (justAttack) {
      if (hasInteractableNear()) {
        interact();
      } else {
        shoot();
      }
      justAttack = false;
    }
    if (mouse.down) {
      shoot();
    }
    if (justInteract) {
      interact();
      justInteract = false;
    }
    if (justDeploy) {
      deployHwacha();
      justDeploy = false;
    }

    if (state.resources.grain <= 0) {
      state.resources.morale -= dt * 2;
    }
    if (state.resources.morale <= 0 || state.player.hp <= 0 || (state.gate && state.gate.hp <= 0)) {
      fail("전열이 무너졌습니다. R로 다시 시도하십시오.");
    }
    if (state.cart && state.cart.hp <= 0) {
      fail("보급 수레를 잃었습니다. R로 다시 시도하십시오.");
    }

    if (checkMissionSuccess(mission)) {
      success();
    }
  }

  function movePlayer(dt) {
    const p = state.player;
    let dx = 0;
    let dy = 0;
    if (keys.has("a") || keys.has("arrowleft")) dx -= 1;
    if (keys.has("d") || keys.has("arrowright")) dx += 1;
    if (keys.has("w") || keys.has("arrowup")) dy -= 1;
    if (keys.has("s") || keys.has("arrowdown")) dy += 1;
    const len = Math.hypot(dx, dy) || 1;
    dx /= len;
    dy /= len;
    if (dx || dy) {
      p.facingX = dx;
      p.facingY = dy;
    }
    p.x = clamp(p.x + dx * p.speed * dt, 34, W - 34);
    p.y = clamp(p.y + dy * p.speed * dt, 74, H - 34);
  }

  function updateCivilians(dt) {
    for (const civilian of state.civilians) {
      if (civilian.rescued) continue;
      const near = dist(civilian, state.player) < 34;
      civilian.panic = Math.max(0, civilian.panic + (near ? -2 : 0.5) * dt);
      if (near && justInteract) {
        civilian.rescued = true;
        state.rescued += 1;
        state.resources.morale = clamp(state.resources.morale + 6, 0, 100);
        setMessage("피난민을 북문 길로 보냈습니다.");
        burst(civilian.x, civilian.y, "#f0dca5", 8);
      }
    }
  }

  function updateEnemies(dt) {
    for (const enemy of state.enemies) {
      const target = chooseEnemyTarget(enemy);
      const dx = target.x - enemy.x;
      const dy = target.y - enemy.y;
      const len = Math.hypot(dx, dy) || 1;
      const speed = enemy.type === "gunner" ? 44 : enemy.type === "runner" ? 76 : 58;
      enemy.x += (dx / len) * speed * dt;
      enemy.y += (dy / len) * speed * dt;
      enemy.attackCd -= dt;

      if (dist(enemy, state.player) < enemy.r + state.player.r + 4 && enemy.attackCd <= 0) {
        state.player.hp -= enemy.type === "runner" ? 9 : 7;
        enemy.attackCd = 0.8;
        burst(state.player.x, state.player.y, "#c7442e", 5);
      }
      if (state.gate && dist(enemy, state.gate) < 46 && enemy.attackCd <= 0) {
        state.gate.hp -= enemy.type === "runner" ? 9 : 6;
        enemy.attackCd = 1.0;
        burst(state.gate.x, state.gate.y, "#7a3827", 4);
      }
      if (state.cart && dist(enemy, state.cart) < 48 && enemy.attackCd <= 0) {
        state.cart.hp -= 8;
        enemy.attackCd = 1.0;
        burst(state.cart.x, state.cart.y, "#a67b45", 4);
      }
    }
    state.enemies = state.enemies.filter((enemy) => enemy.hp > 0 && enemy.x > -60 && enemy.y > 30 && enemy.y < H + 60);
  }

  function chooseEnemyTarget(enemy) {
    if (state.cart) return state.cart;
    if (state.gate) return state.gate;
    return state.player;
  }

  function updateProjectiles(dt) {
    for (const projectile of state.projectiles) {
      projectile.x += projectile.vx * dt;
      projectile.y += projectile.vy * dt;
      projectile.life -= dt;
      if (projectile.team === "joseon") {
        for (const enemy of state.enemies) {
          if (dist(projectile, enemy) < projectile.r + enemy.r) {
            enemy.hp -= projectile.damage;
            projectile.life = 0;
            burst(enemy.x, enemy.y, projectile.color, 5);
            if (enemy.hp <= 0) {
              state.kills += 1;
              state.resources.morale = clamp(state.resources.morale + 1.5, 0, 100);
            }
            break;
          }
        }
      }
    }
    state.projectiles = state.projectiles.filter((p) => p.life > 0 && p.x > -40 && p.x < W + 40 && p.y > -40 && p.y < H + 40);
  }

  function updateParticles(dt) {
    for (const particle of state.particles) {
      particle.x += particle.vx * dt;
      particle.y += particle.vy * dt;
      particle.life -= dt;
      particle.size *= 0.985;
    }
    state.particles = state.particles.filter((p) => p.life > 0);
  }

  function updateSpawning(dt) {
    const mission = currentMission();
    state.spawnTimer -= dt;
    if (state.spawnTimer <= 0 && state.enemies.length < mission.enemyLimit) {
      spawnEnemy();
      const pressure = 1 - Math.min(0.45, state.time / 180);
      state.spawnTimer = Math.max(0.65, mission.spawnRate * pressure + Math.random() * 0.45);
    }
  }

  function spawnEnemy() {
    const roll = Math.random();
    const type = roll > 0.72 ? "gunner" : roll > 0.48 ? "runner" : "spearman";
    const y = 100 + Math.random() * 430;
    state.enemies.push({
      type,
      x: W + 24,
      y,
      r: type === "runner" ? 10 : 12,
      hp: type === "gunner" ? 18 : type === "runner" ? 14 : 22,
      attackCd: 0.5 + Math.random(),
    });
  }

  function shoot() {
    const p = state.player;
    if (p.shootCd > 0) return;
    let dx = mouse.x - p.x;
    let dy = mouse.y - p.y;
    if (!mouse.down && Math.hypot(dx, dy) > 220) {
      dx = p.facingX;
      dy = p.facingY;
    }
    if (!mouse.down) {
      const nearest = nearestEnemy();
      if (nearest && dist(nearest, p) < 260) {
        dx = nearest.x - p.x;
        dy = nearest.y - p.y;
      }
    }
    const len = Math.hypot(dx, dy) || 1;
    state.projectiles.push({
      team: "joseon",
      x: p.x + (dx / len) * 18,
      y: p.y + (dy / len) * 18,
      vx: (dx / len) * 360,
      vy: (dy / len) * 360,
      r: 4,
      damage: 12,
      life: 0.9,
      color: "#e6c66f",
    });
    p.shootCd = 0.28;
  }

  function nearestEnemy() {
    let best = null;
    let bestDist = Infinity;
    for (const enemy of state.enemies) {
      const d = dist(enemy, state.player);
      if (d < bestDist) {
        best = enemy;
        bestDist = d;
      }
    }
    return best;
  }

  function interact() {
    const p = state.player;
    for (const crate of state.crates) {
      if (!crate.taken && dist(crate, p) < 34) {
        crate.taken = true;
        if (crate.type === "powder") state.resources.powder += 2;
        if (crate.type === "timber") state.resources.timber += 2;
        if (crate.type === "grain") state.resources.grain += 2;
        if (crate.type === "dispatch") {
          state.dispatch = true;
          state.resources.morale = clamp(state.resources.morale + 8, 0, 100);
        }
        setMessage(resourceMessage(crate.type));
        burst(crate.x, crate.y, "#e6c66f", 9);
        return;
      }
    }
    for (const civilian of state.civilians) {
      if (!civilian.rescued && dist(civilian, p) < 34) {
        civilian.rescued = true;
        state.rescued += 1;
        setMessage("피난민을 안전한 북문 길로 보냈습니다.");
        burst(civilian.x, civilian.y, "#f0dca5", 8);
        return;
      }
    }
    if (state.gate && dist(state.gate, p) < 56 && state.resources.timber > 0 && state.gate.hp < state.gate.max) {
      state.resources.timber -= 1;
      state.gate.hp = clamp(state.gate.hp + 28, 0, state.gate.max);
      setMessage("목재로 성문을 보강했습니다.");
      burst(state.gate.x, state.gate.y, "#b88d55", 8);
      return;
    }
    if (state.beacon && dist(state.beacon, p) < 42) {
      state.beacon.lit = true;
      setMessage("봉화가 전라좌수영 방향으로 이어졌습니다. 이순신 장군은 살아 있습니다.");
      burst(state.beacon.x, state.beacon.y, "#ffb247", 12);
      return;
    }
    if (state.cart && dist(state.cart, p) < 50 && state.resources.timber > 0 && state.cart.hp < state.cart.max) {
      state.resources.timber -= 1;
      state.cart.hp = clamp(state.cart.hp + 24, 0, state.cart.max);
      setMessage("보급 수레 축을 고쳤습니다.");
      burst(state.cart.x, state.cart.y, "#b88d55", 8);
    }
  }

  function hasInteractableNear() {
    const p = state.player;
    if (state.crates.some((crate) => !crate.taken && dist(crate, p) < 34)) return true;
    if (state.civilians.some((civilian) => !civilian.rescued && dist(civilian, p) < 34)) return true;
    if (state.gate && dist(state.gate, p) < 56 && state.resources.timber > 0 && state.gate.hp < state.gate.max) return true;
    if (state.beacon && dist(state.beacon, p) < 42) return true;
    if (state.cart && dist(state.cart, p) < 50 && state.resources.timber > 0 && state.cart.hp < state.cart.max) return true;
    return false;
  }

  function resourceMessage(type) {
    return {
      powder: "화약을 확보했습니다. Q로 화차를 배치할 수 있습니다.",
      timber: "목재를 확보했습니다. 성문과 수레를 고칠 수 있습니다.",
      grain: "군량을 확보했습니다. 사기가 회복됩니다.",
      dispatch: "장계를 확보했습니다. 동래성과 전라좌수영으로 이어집니다.",
    }[type];
  }

  function deployHwacha() {
    if (state.player.hwachaCd > 0) return;
    if (state.resources.powder < 2) {
      setMessage("화약이 부족합니다.");
      return;
    }
    state.resources.powder -= 2;
    state.player.hwachaCd = 5.5;
    setMessage("화차 발사. 성문 앞 접근을 막습니다.");
    const p = state.player;
    for (let i = 0; i < 14; i++) {
      const angle = -0.42 + (i / 13) * 0.84;
      const base = Math.atan2(p.facingY, p.facingX);
      const vx = Math.cos(base + angle) * 470;
      const vy = Math.sin(base + angle) * 470;
      state.projectiles.push({
        team: "joseon",
        x: p.x,
        y: p.y,
        vx,
        vy,
        r: 4,
        damage: 17,
        life: 0.75,
        color: "#ff8a3c",
      });
    }
    burst(p.x, p.y, "#ff8a3c", 18);
  }

  function checkMissionSuccess(mission) {
    if (mission.id === "busanjin") {
      return state.time >= mission.duration && state.rescued >= mission.goal.rescued && state.dispatch;
    }
    if (mission.id === "dongnae") {
      return state.time >= mission.duration && state.rescued >= mission.goal.rescued && state.beacon.lit;
    }
    if (mission.id === "seed") {
      return state.time >= mission.duration && state.kills >= mission.goal.kills && state.cart && state.cart.hp > 0;
    }
    return false;
  }

  function success() {
    const mission = currentMission();
    if (state.mode !== "playing") return;
    state.mode = "success";
    state.result =
      mission.id === "seed"
        ? "반격의 씨앗을 지켰습니다. 조선은 아직 무너지지 않았습니다."
        : "다음 장으로 이어질 자원을 살렸습니다.";
  }

  function fail(reason) {
    if (state.mode !== "playing") return;
    state.mode = "defeat";
    state.result = reason;
  }

  function setMessage(text) {
    state.message = text;
    state.messageTimer = 4;
  }

  function burst(x, y, color, count) {
    for (let i = 0; i < count; i++) {
      const a = Math.random() * Math.PI * 2;
      const s = 30 + Math.random() * 80;
      state.particles.push({
        x,
        y,
        vx: Math.cos(a) * s,
        vy: Math.sin(a) * s,
        size: 3 + Math.random() * 4,
        color,
        life: 0.35 + Math.random() * 0.45,
      });
    }
  }

  function render() {
    drawBackground();
    if (state.mode === "menu") return;
    drawMap();
    drawObjects();
    drawUnits();
    drawProjectiles();
    drawParticles();
    drawUi();
    if (state.mode === "briefing") drawOverlay(currentMission().title, currentMission().briefing, "Enter 또는 클릭으로 시작");
    if (state.mode === "success") drawOverlay("목표 달성", state.result, nextText());
    if (state.mode === "defeat") drawOverlay("전열 붕괴", state.result, "R로 재시작");
    if (state.mode === "complete") drawOverlay("파일럿 완료", "부산진-동래성-반격의 씨앗을 모두 진행했습니다.", "R로 다시 플레이");
  }

  function drawBackground() {
    ctx.fillStyle = "#2a2318";
    ctx.fillRect(0, 0, W, H);
    for (let y = 78; y < H; y += 42) {
      ctx.fillStyle = y % 84 === 0 ? "#302819" : "#2e2618";
      ctx.fillRect(0, y, W, 18);
    }
    ctx.fillStyle = "#47351f";
    ctx.fillRect(90, 70, 760, 530);
    ctx.fillStyle = "#5c4626";
    for (let i = 0; i < 18; i++) {
      ctx.fillRect(110 + i * 42, 340 + Math.sin(i) * 14, 28, 9);
    }
    ctx.fillStyle = "rgba(80, 64, 43, 0.58)";
    ctx.fillRect(96, 438, 790, 54);
  }

  function drawMap() {
    ctx.fillStyle = "#3c3226";
    ctx.fillRect(0, 0, W, 64);
    ctx.fillStyle = "#22201d";
    ctx.fillRect(0, 64, 76, H - 64);
    ctx.fillStyle = "#473d32";
    ctx.fillRect(74, 64, 14, H - 64);
    ctx.fillStyle = "#1e2b25";
    ctx.fillRect(770, 70, 190, H - 70);
    ctx.fillStyle = "#303829";
    for (let i = 0; i < 12; i++) {
      ctx.fillRect(790 + (i % 4) * 44, 96 + Math.floor(i / 4) * 76, 18, 46);
    }
  }

  function drawObjects() {
    const mission = currentMission();
    if (state.gate) {
      ctx.fillStyle = "#181411";
      ctx.fillRect(state.gate.x - 18, state.gate.y - state.gate.h / 2, state.gate.w, state.gate.h);
      ctx.fillStyle = "#8a5b33";
      ctx.fillRect(state.gate.x - 10, state.gate.y - state.gate.h / 2 + 10, 26, state.gate.h - 20);
      drawBar(state.gate.x - 28, state.gate.y - state.gate.h / 2 - 18, 70, 7, state.gate.hp / state.gate.max, "#c47a42");
    }
    if (state.cart) {
      drawCart(state.cart.x, state.cart.y);
      drawBar(state.cart.x - 34, state.cart.y - 34, 72, 7, state.cart.hp / state.cart.max, "#d49b52");
    }
    drawBeacon(state.beacon.x, state.beacon.y, state.beacon.lit);
    for (const crate of state.crates) {
      if (!crate.taken) drawCrate(crate);
    }
    ctx.fillStyle = "rgba(226, 191, 116, 0.12)";
    ctx.fillRect(84, 88, 86, 420);
    if (mission.id === "seed") {
      ctx.fillStyle = "rgba(81, 111, 73, 0.22)";
      ctx.fillRect(240, 400, 550, 82);
    }
  }

  function drawUnits() {
    for (const civilian of state.civilians) {
      if (!civilian.rescued) drawCivilian(civilian.x, civilian.y);
    }
    for (const enemy of state.enemies) {
      drawEnemy(enemy);
    }
    drawPlayer(state.player.x, state.player.y);
  }

  function drawPlayer(x, y) {
    ctx.save();
    ctx.translate(x, y);
    ctx.fillStyle = "#1f5d83";
    ctx.beginPath();
    ctx.arc(0, 0, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#e6d6b0";
    ctx.fillRect(-6, -22, 12, 10);
    ctx.fillStyle = "#af3127";
    ctx.fillRect(-3, -20, 6, 24);
    ctx.strokeStyle = "#e8c56b";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(state.player.facingX * 18, state.player.facingY * 18);
    ctx.stroke();
    ctx.restore();
  }

  function drawEnemy(enemy) {
    ctx.save();
    ctx.translate(enemy.x, enemy.y);
    ctx.fillStyle = enemy.type === "gunner" ? "#3a1c1c" : enemy.type === "runner" ? "#6b2a26" : "#4c2323";
    ctx.beginPath();
    ctx.moveTo(14, 0);
    ctx.lineTo(-10, 12);
    ctx.lineTo(-8, -12);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "#c5b48e";
    if (enemy.type === "gunner") ctx.fillRect(-18, -3, 24, 6);
    if (enemy.type === "runner") ctx.fillRect(-12, -16, 6, 32);
    ctx.restore();
  }

  function drawCivilian(x, y) {
    ctx.fillStyle = "#e5d8bc";
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#7d6e54";
    ctx.fillRect(x - 5, y + 7, 10, 10);
  }

  function drawCrate(crate) {
    const colors = {
      powder: "#69533b",
      timber: "#8a5a34",
      grain: "#b99557",
      dispatch: "#d8c594",
    };
    ctx.fillStyle = colors[crate.type];
    ctx.fillRect(crate.x - 12, crate.y - 12, 24, 24);
    ctx.strokeStyle = "#1b1711";
    ctx.lineWidth = 2;
    ctx.strokeRect(crate.x - 12, crate.y - 12, 24, 24);
    ctx.fillStyle = "#f5e6b6";
    ctx.font = "12px Malgun Gothic";
    ctx.textAlign = "center";
    ctx.fillText({ powder: "화", timber: "목", grain: "량", dispatch: "계" }[crate.type], crate.x, crate.y + 4);
  }

  function drawBeacon(x, y, lit) {
    ctx.fillStyle = "#5d5a4f";
    ctx.fillRect(x - 16, y + 8, 32, 22);
    ctx.fillStyle = "#2e2a22";
    ctx.fillRect(x - 20, y + 28, 40, 8);
    if (lit) {
      ctx.fillStyle = "#ffb247";
      ctx.beginPath();
      ctx.moveTo(x, y - 24);
      ctx.lineTo(x + 16, y + 12);
      ctx.lineTo(x - 16, y + 12);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "rgba(255, 137, 52, 0.28)";
      ctx.beginPath();
      ctx.arc(x, y, 46, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = "#514b42";
      ctx.beginPath();
      ctx.arc(x, y, 13, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawCart(x, y) {
    ctx.fillStyle = "#8d6334";
    ctx.fillRect(x - 30, y - 16, 60, 30);
    ctx.fillStyle = "#2b2116";
    ctx.beginPath();
    ctx.arc(x - 20, y + 18, 8, 0, Math.PI * 2);
    ctx.arc(x + 20, y + 18, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#d6b372";
    ctx.fillRect(x - 18, y - 24, 36, 10);
  }

  function drawProjectiles() {
    for (const projectile of state.projectiles) {
      ctx.fillStyle = projectile.color;
      ctx.beginPath();
      ctx.arc(projectile.x, projectile.y, projectile.r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawParticles() {
    for (const particle of state.particles) {
      ctx.globalAlpha = clamp(particle.life * 2, 0, 1);
      ctx.fillStyle = particle.color;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  function drawUi() {
    const mission = currentMission();
    ctx.fillStyle = "rgba(22, 18, 13, 0.9)";
    ctx.fillRect(0, 0, W, 64);
    ctx.fillStyle = "#f1d18e";
    ctx.font = "700 18px Malgun Gothic";
    ctx.textAlign = "left";
    ctx.fillText(`${mission.title}  ${mission.date}`, 18, 26);
    ctx.fillStyle = "#d9c8aa";
    ctx.font = "13px Malgun Gothic";
    ctx.fillText(mission.objective, 18, 48);

    drawBar(700, 12, 104, 8, state.player.hp / 100, "#c94e3a");
    drawBar(700, 32, 104, 8, state.resources.morale / 100, "#d6a94d");
    ctx.fillStyle = "#eadfca";
    ctx.font = "12px Malgun Gothic";
    ctx.fillText("체력", 652, 20);
    ctx.fillText("사기", 652, 40);
    ctx.fillText(`화약 ${state.resources.powder} 목재 ${state.resources.timber} 군량 ${state.resources.grain}`, 818, 23);
    ctx.fillText(`구출 ${state.rescued} 격퇴 ${state.kills}`, 818, 43);

    ctx.fillStyle = "#8fcf9d";
    ctx.fillText("전라좌수영: 이순신 장군 생존", 18, H - 18);
    if (state.messageTimer > 0 || state.message) {
      ctx.fillStyle = "rgba(30, 25, 18, 0.86)";
      ctx.fillRect(230, H - 42, 500, 28);
      ctx.fillStyle = "#f7e9c9";
      ctx.textAlign = "center";
      ctx.font = "13px Malgun Gothic";
      ctx.fillText(state.message, 480, H - 23);
    }
  }

  function drawBar(x, y, w, h, ratio, color) {
    ctx.fillStyle = "#191510";
    ctx.fillRect(x, y, w, h);
    ctx.fillStyle = color;
    ctx.fillRect(x, y, w * clamp(ratio, 0, 1), h);
    ctx.strokeStyle = "#e6d0a6";
    ctx.strokeRect(x, y, w, h);
  }

  function drawOverlay(title, body, hint) {
    ctx.fillStyle = "rgba(18, 15, 11, 0.82)";
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "#f0cf8d";
    ctx.font = "700 34px Malgun Gothic";
    ctx.textAlign = "center";
    ctx.fillText(title, W / 2, 205);
    ctx.fillStyle = "#eee0c4";
    ctx.font = "17px Malgun Gothic";
    wrapText(body, W / 2, 245, 650, 28);
    ctx.fillStyle = "#e39b4b";
    ctx.font = "700 16px Malgun Gothic";
    ctx.fillText(hint, W / 2, 355);
    ctx.fillStyle = "#9dd89e";
    ctx.font = "14px Malgun Gothic";
    ctx.fillText("이순신 장군 생존 고정: 장계와 봉화가 전라좌수영으로 이어집니다.", W / 2, 392);
  }

  function nextText() {
    return state.missionIndex + 1 >= missions.length ? "Enter로 완료 화면" : "Enter 또는 클릭으로 다음 장";
  }

  function wrapText(text, x, y, maxWidth, lineHeight) {
    const words = text.split(" ");
    let line = "";
    let yy = y;
    for (const word of words) {
      const test = line + word + " ";
      if (ctx.measureText(test).width > maxWidth && line.length > 0) {
        ctx.fillText(line, x, yy);
        line = word + " ";
        yy += lineHeight;
      } else {
        line = test;
      }
    }
    ctx.fillText(line, x, yy);
  }

  function dist(a, b) {
    const bx = b.x;
    const by = b.y;
    return Math.hypot(a.x - bx, a.y - by);
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function renderGameToText() {
    const mission = currentMission();
    return JSON.stringify({
      coordinateSystem: "origin top-left, x right, y down, canvas 960x600",
      mode: state.mode,
      mission: mission ? mission.title : "menu",
      time: Math.round(state.time),
      player: {
        x: Math.round(state.player.x),
        y: Math.round(state.player.y),
        hp: Math.round(state.player.hp),
      },
      yiSunSinAlive: true,
      resources: state.resources,
      gateHp: state.gate ? Math.round(state.gate.hp) : null,
      cartHp: state.cart ? Math.round(state.cart.hp) : null,
      beaconLit: !!state.beacon?.lit,
      dispatchSecured: !!state.dispatch,
      rescued: state.rescued,
      kills: state.kills,
      enemies: state.enemies.map((e) => ({
        type: e.type,
        x: Math.round(e.x),
        y: Math.round(e.y),
        hp: Math.round(e.hp),
      })),
      objective: mission?.objective,
      result: state.result,
    });
  }

  window.render_game_to_text = renderGameToText;
  window.advanceTime = (ms) => {
    const steps = Math.max(1, Math.round(ms / (1000 / 60)));
    for (let i = 0; i < steps; i++) {
      update(1 / 60);
    }
    render();
  };

  function gameLoop(timestamp) {
    const dt = Math.min(0.05, (timestamp - lastTime) / 1000 || 0);
    lastTime = timestamp;
    update(dt);
    render();
    requestAnimationFrame(gameLoop);
  }

  render();
  requestAnimationFrame(gameLoop);

  window.__imjinFanGame = {
    startMission,
    beginPlay,
    restartMission,
    facts,
    missions,
  };
})();
