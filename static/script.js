const cells = document.querySelectorAll(".cell");
const message = document.querySelector("#message");

const playerSymbols = ["X", "O"];
const turnMessages = ["X Turn", "O Turn"];

const resultMessages = ["X Wins!", "O Wins!", "Draw!"];
const DRAW = 2;


// ------------------------------------------------
// Flaskとの通信　＝＞　app.py
// ------------------------------------------------

async function post(url) {
  const response = await fetch(url, { method: "POST" });
  return response.json();
}


// ------------------------------------------------
// ウェブページの更新
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
}

function displayWinnerCells(pattern) {
  pattern.forEach((position) => {
    cells[position].classList.add("winner");
  });
}

function clearStyles() {
  message.classList.remove("winner-message");
  cells.forEach((cell) => {
    cell.classList.remove("winner");
  });
}


// ------------------------------------------------
// サーバーの返答　⇒　レンダリング
// ------------------------------------------------

function render(state) {
  clearStyles();
  updateCells(state.cells);

  if (state.game_running) {
    displayMessage(turnMessages[state.player]);
  } else if (state.winning_pattern) {
    displayFinishedMessage(resultMessages[state.player]);
    displayWinnerCells(state.winning_pattern);
  } else {
    displayFinishedMessage(resultMessages[DRAW]);
  }
}


// ------------------------------------------------
// ゲーム操作
// ------------------------------------------------

async function startGame() {
  render(await post("/api/start"));
}

async function cellClick(position) {
  render(await post(`/api/play/${position}`));
}


// ------------------------------------------------
// 初期化
// ------------------------------------------------

cells.forEach((cell, i) => {
  cell.addEventListener("click", () => cellClick(i));
});

startGame();