const cells = document.querySelectorAll(".cell");
const message = document.querySelector("#message");
const restartButton = document.querySelector("#restart");

const playerSymbols = ["X", "O"];
const turnMessages = ["X Turn", "O Turn"];

const resultMessages = ["X Wins!", "O Wins!", "Draw!"];
const DRAW = 2;

let gameOver = false;


// ------------------------------------------------
// Flaskとの通信　＝＞　app.py
// ------------------------------------------------

async function post(url) {
  const response = await fetch(url, { method: "POST" });
  return response.json();
}


// ------------------------------------------------
// 画面更新用の関数
// ------------------------------------------------

function updateCells(values) {
  values.forEach((value, i) => {
    cells[i].textContent = value === null ? "" : playerSymbols[value];
  });
}

function displayMessage(value) {
  message.textContent = value;
}

function displayFinishedMessage(value) {
  message.textContent = value;
  message.classList.add("winner-message");
  restartButton.classList.remove("hidden");
}

function displayWinnerCells(pattern) {
  pattern.forEach((position) => {
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
// ゲーム操作
// ------------------------------------------------

async function loadGame() {
  const response = await fetch("/api/state");
  render(await response.json());
}

async function startGame() {
  render(await post("/api/start"));
}

async function cellClick(position) {
  if (gameOver) return;
  render(await post(`/api/play/${position}`));
}


// ------------------------------------------------
// 初期化 & イベント登録
// ------------------------------------------------

cells.forEach((cell, i) => {
  cell.addEventListener("click", () => cellClick(i));
});

restartButton.addEventListener("click", startGame);

loadGame();