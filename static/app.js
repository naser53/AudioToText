const form = document.getElementById("form");
const statusBox = document.getElementById("status");
const stage = document.getElementById("stage");
const bar = document.getElementById("bar");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.hidden = false;
  form.querySelector("button").disabled = false;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  form.querySelector("button").disabled = true;
  statusBox.hidden = false;
  errorBox.hidden = true;
  result.hidden = true;
  stage.textContent = "Uploading…";
  bar.value = 0;

  const res = await fetch("/jobs", { method: "POST", body: new FormData(form) });
  const data = await res.json();
  if (!res.ok) return showError(data.error || "Upload failed.");
  poll(data.id);
});

async function poll(id) {
  const res = await fetch(`/jobs/${id}`);
  const job = await res.json();
  if (job.status === "error") return showError(job.error);
  stage.textContent = job.status === "done" ? "Done" : `${job.stage}… ${job.progress}%`;
  bar.value = job.progress;
  if (job.status === "done") {
    document.getElementById("download").href = `/jobs/${id}/download`;
    document.getElementById("download").textContent = `Download ${job.output_name}`;
    document.getElementById("preview").textContent = job.preview;
    result.hidden = false;
    form.querySelector("button").disabled = false;
    return;
  }
  setTimeout(() => poll(id), 1000);
}
