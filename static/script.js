const cells = document.querySelectorAll(".cell");
const message = document.querySelector("#message");
const restartButton = document.querySelector("#restart");

const playerSymbols = ["X", "O"]; // 0 = X, 1 = O
const turnMessages = ["X Turn", "O Turn"];

const resultMessages = ["X Wins!", "O Wins!", "Draw!"];
const DRAW = 2;  // 0 = X Wins, 1 = O Wins, 2 = Draw

let gameOver = false;
let busy = false;
let syncFailed = false;


// ------------------------------------------------
// 通信失敗後の再同期ボタン
// ------------------------------------------------

const syncButton = document.createElement("button");

syncButton.type = "button";
syncButton.textContent = "RetrySync";
syncButton.classList.add("sync-button");
syncButton.hidden = true;
message.insertAdjacentElement("afterend", syncButton);


// ------------------------------------------------
// Flaskとの通信　＝＞　app.py
// ------------------------------------------------

async function requestJSON(url, options = {}) {
  const response = await fetch(url, options);

  // HTTPエラーを例外として扱う
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  // JSONの解析に失敗した場合も例外が発生する
  return response.json();
}

async function post(url) {
  return requestJSON(url, { method: "POST" });
}


// ------------------------------------------------
// サーバーから返されたデータの検証
// ------------------------------------------------

function validateState(state) {
  if (
    state === null ||
    typeof state !== "object" ||
    Array.isArray(state)
  ) {
    throw new Error("Invalid game state");
  }

  if (typeof state.game_running !== "boolean") {
    throw new Error("Invalid game_running");
  }

  if (!Array.isArray(state.cells) || state.cells.length !== 9) {
    throw new Error("Invalid cells");
  }

  if (!state.cells.every(
    (cell) => cell === null || cell === 0 || cell === 1
  )) {
    throw new Error("Invalid cell value");
  }

  if (state.player !== 0 && state.player !== 1) {
    throw new Error("Invalid player");
  }

  if (!["playing", "win", "draw"].includes(state.status)) {
    throw new Error("Invalid status");
  }

  if (state.status === "playing" && !state.game_running) {
    throw new Error("Invalid playing state");
  }

  if (state.status !== "playing" && state.game_running) {
    throw new Error("Invalid finished state");
  }

  if (state.status === "win") {
    if (state.winner !== 0 && state.winner !== 1) {
      throw new Error("Invalid winner");
    }

    if (
      !Array.isArray(state.winning_pattern) ||
      state.winning_pattern.length !== 3 ||
      !state.winning_pattern.every(
        (position) =>
          Number.isInteger(position) &&
          position >= 0 &&
          position < 9
      ) ||
      new Set(state.winning_pattern).size !== 3
    ) {
      throw new Error("Invalid winning_pattern");
    }
  }
}


// ------------------------------------------------
// 画面更新用の関数
// ------------------------------------------------

function updateCells(symbols) {
  symbols.forEach((symbol, position) => {
    cells[position].textContent =
      symbol === null ? "" : playerSymbols[symbol];
  });
}

function displayMessage(turnMessage) {
  message.textContent = turnMessage;
}

function displayFinishedMessage(resultMessage) {
  message.textContent = resultMessage;
  message.classList.add("winner-message");
  restartButton.classList.remove("hidden");
}

function displayWinnerCells(symbols) {
  symbols.forEach((position) => {
    cells[position].classList.add("winner");
  });
}

function clearStyles() {
  message.classList.remove("winner-message");
  restartButton.classList.add("hidden");

  cells.forEach((cell) => {
    cell.classList.remove("winner");
  });
}


// ------------------------------------------------
// サーバーから返された状態を画面に反映
// ------------------------------------------------

function render(state) {
  gameOver = !state.game_running;

  clearStyles();
  updateCells(state.cells);

  if (state.status === "playing") {
    displayMessage(turnMessages[state.player]);
  } else if (state.status === "win") {
    displayFinishedMessage(resultMessages[state.winner]);
    displayWinnerCells(state.winning_pattern);
  } else {
    displayFinishedMessage(resultMessages[DRAW]);
  }
}


// ------------------------------------------------
// 操作状態の更新
// ------------------------------------------------

function updateControls() {
  cells.forEach((cell) => {
    cell.disabled = busy || gameOver || syncFailed;
  });

  restartButton.disabled = busy || syncFailed;
  syncButton.disabled = busy;
  syncButton.hidden = !syncFailed;
}


// ------------------------------------------------
// リクエストの実行とエラー処理
// ------------------------------------------------

async function runRequest(action, allowFailed = false) {
  if (busy || (syncFailed && !allowFailed)) return;

  busy = true;
  updateControls();

  try {
    await action();
  } catch (error) {
    console.error("通信エラー:", error);

    // 結果が不明な操作を繰り返さない
    syncFailed = true;

    message.classList.remove("winner-message");
    message.textContent =
      "通信に失敗しました。RetrySyncでゲームの状態を再取得してください。";
  } finally {
    busy = false;
    updateControls();
  }
}


// ------------------------------------------------
// ゲーム操作
// ------------------------------------------------

async function loadGame() {
  await runRequest(async () => {
    const state = await requestJSON("/api/state");

    validateState(state);

    render(state);
    syncFailed = false;
  }, true);
}

async function startGame() {
  await runRequest(async () => {
    const state = await post("/api/start");

    validateState(state);

    render(state);
    syncFailed = false;
  });
}

async function cellClick(position) {
  if (gameOver || syncFailed) return;

  await runRequest(async () => {
    const state = await post(`/api/play/${position}`);

    validateState(state);
    render(state);
  });
}


// ------------------------------------------------
// 初期化 & イベント登録
// ------------------------------------------------

cells.forEach((cell, i) => {
  cell.addEventListener("click", () => cellClick(i));
});

restartButton.addEventListener("click", startGame);
syncButton.addEventListener("click", loadGame);

loadGame();