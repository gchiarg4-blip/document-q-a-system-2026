let kbId = null;
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');
uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault(); uploadStatus.className='status'; uploadStatus.textContent='Uploading and building knowledge base...';
  const data = new FormData(); data.append('file', document.getElementById('file').files[0]);
  try {
    const response = await fetch('/upload', {method:'POST', body:data});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Upload failed.');
    kbId = result.kb_id;
    uploadStatus.className='status success';
    uploadStatus.textContent = `${result.message} ${result.record_count} text records created.`;
  } catch(err) { uploadStatus.className='status error'; uploadStatus.textContent=err.message; }
});
document.getElementById('ask-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const output = document.getElementById('answer');
  if (!kbId) { output.textContent='Upload a document first.'; return; }
  output.textContent='Searching...';
  try {
    const response = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({question:document.getElementById('question').value, kb_id:kbId})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Question failed.');
    output.textContent = `Answer: ${result.answer}\n\nMatching evidence:\n` +
      (result.matches || []).map(m=>`• ${m.text} (${m.source}; score ${m.score})`).join('\n');
  } catch(err) { output.textContent=err.message; }
});
