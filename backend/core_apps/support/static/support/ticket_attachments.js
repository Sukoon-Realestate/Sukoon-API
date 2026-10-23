/* The existing operator form attaches only server-inspected uploads. */
window.addEventListener('DOMContentLoaded', () => {
  const ids = document.getElementById('id_attachment_ids');
  if (!ids) return;
  const form = ids.form;
  const ticket = location.pathname.match(/ticket\/([0-9a-f-]+)\/change/);
  if (!ticket) return;
  const picker = document.createElement('input'); picker.type = 'file'; picker.multiple = true;
  picker.id = 'support_attachment_picker';
  picker.accept = 'image/png,image/jpeg,image/webp,application/pdf,video/mp4,video/quicktime';
  const status = document.createElement('p'); status.setAttribute('role','status');
  const label = document.createElement('label'); label.htmlFor = picker.id;
  label.textContent = 'Attachments: images 5 MB, PDF 25 MB, video 50 MB / 5 minutes';
  const row = document.createElement('div'); row.className = 'form-row';
  row.append(label, picker, status);
  // Django hides the entire form row containing HiddenInput, including its
  // inner flex container. Place the picker beside that row so it is usable.
  const hiddenRow = ids.closest('.form-row');
  if (hiddenRow) hiddenRow.after(row); else ids.parentElement.append(row);
  let busy = false;
  form.addEventListener('submit', event => { if (busy) { event.preventDefault(); status.textContent = 'Wait for attachment inspection.'; } });
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  picker.addEventListener('change', async () => {
    if (busy) return;
    const files = Array.from(picker.files); if (files.length > 3) { status.textContent = 'Choose up to three files.'; return; }
    busy = true; picker.disabled = true; ids.value = '';
    try {
      const workspace = ids.dataset.workspace;
      if (!['owner', 'tenant'].includes(workspace)) throw new Error('Refresh the ticket before uploading attachments.');
      const uploaded = [];
      for (const file of files) {
        const identity = crypto.randomUUID();
        const body = new FormData(); body.append('client_upload_id',identity); body.append('ticket_id',ticket[1]);
        body.append('workspace',workspace); body.append('file',file);
        let response = await fetch('/api/v1/support/uploads/',{method:'POST',headers:{'X-CSRFToken':csrf},body});
        if (!response.ok) throw new Error('Upload was rejected. Check type, size and ticket access.');
        let data = (await response.json()).data;
        for (let attempt=0; data.status==='pending' && attempt<90; attempt++) {
          status.textContent = 'Inspecting ' + file.name;
          await new Promise(resolve=>setTimeout(resolve,2000));
          response = await fetch('/api/v1/support/uploads/'+identity+'/');
          if (!response.ok) throw new Error('Could not confirm attachment status.');
          data = (await response.json()).data;
        }
        if (data.status!=='ready') throw new Error('Attachment is not ready. Retry after inspection or choose another file.');
        uploaded.push(data.id);
      }
      ids.value=uploaded.join(','); status.textContent='Attachments ready. Review and send the reply.';
    } catch(error) { status.textContent=error.message; }
    finally { busy=false; picker.disabled=false; }
  });
});
