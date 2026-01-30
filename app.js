const LS_KEY = 'smartPawPets';
let stream = null;

function loadPets(){
  try{
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : [];
  }catch(e){return []}
}

function savePets(arr){
  localStorage.setItem(LS_KEY, JSON.stringify(arr));
}

function updateHome(){
  const pets = loadPets();
  const count = pets.length;
  document.getElementById('petCount').textContent = count;
  const recent = document.getElementById('recent');
  recent.innerHTML = '';
  if(count===0){
    recent.innerHTML = '<div class="text-muted">No pets registered yet.</div>';
    return;
  }
  const last = pets[pets.length-1];
  const card = document.createElement('div');
  card.className='card';
  card.innerHTML = `
    <div class="card-body d-flex gap-3 align-items-center">
      <img src="${last.photo||''}" alt="photo" style="width:64px;height:64px;object-fit:cover;border-radius:.5rem">
      <div>
        <div class="fw-bold">${last.name}</div>
        <div class="text-muted small">${last.breed} — ${last.owner}</div>
      </div>
    </div>`;
  recent.appendChild(card);
}

function showView(id){
  ['homeView','scanView','registerView'].forEach(v=>{
    const el=document.getElementById(v);
    if(v===id) el.classList.remove('d-none'); else el.classList.add('d-none');
  });
}

async function startCamera(targetVideo){
  if(stream) return;
  try{
    stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}, audio:false});
    targetVideo.srcObject = stream;
    await targetVideo.play();
  }catch(e){console.warn('camera error',e)}
}

function stopCamera(targetVideo){
  if(stream){
    stream.getTracks().forEach(t=>t.stop());
    stream = null;
  }
  try{ targetVideo.pause(); targetVideo.srcObject = null;}catch(e){}
}

function captureFromVideo(video){
  const canvas = document.getElementById('captureCanvas');
  const w = video.videoWidth || 640;
  const h = video.videoHeight || 480;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video,0,0,w,h);
  return canvas.toDataURL('image/jpeg',0.85);
}

function displayPetProfile(pet, target){
  if(!pet){ target.innerHTML = '<div class="text-muted">No match found</div>'; return; }
  target.innerHTML = `
    <div class="card">
      <div class="card-body d-flex gap-3 align-items-center">
        <img src="${pet.photo||''}" alt="photo" style="width:96px;height:96px;object-fit:cover;border-radius:.5rem">
        <div>
          <div class="fw-bold fs-5">${pet.name}</div>
          <div class="text-muted">Breed: ${pet.breed}</div>
          <div class="text-muted">Owner: ${pet.owner}</div>
        </div>
      </div>
    </div>`;
}

document.addEventListener('DOMContentLoaded', ()=>{
  // Navigation
  document.querySelectorAll('.nav-btn').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const target = btn.dataset.target;
      showView(target);
    });
  });

  // init
  updateHome();
  showView('homeView');

  // Register camera flow
  const video = document.getElementById('video');
  const btnOpenCamRegister = document.getElementById('btnOpenCamRegister');
  const photoPreview = document.getElementById('photoPreview');
  const photoData = document.getElementById('photoData');

  btnOpenCamRegister.addEventListener('click', async ()=>{
    // start camera and allow capture, reuse video element
    showView('registerView');
    await startCamera(video);
    document.getElementById('btnStopCamera').classList.remove('d-none');
    document.getElementById('btnOpenCamRegister').textContent = 'Take Photo';
    // temporarily change the click handler to capture
    btnOpenCamRegister.onclick = ()=>{
      const data = captureFromVideo(video);
      photoPreview.src = data; photoPreview.style.display = 'inline-block';
      photoData.value = data;
      stopCamera(video);
      document.getElementById('btnStopCamera').classList.add('d-none');
      btnOpenCamRegister.textContent = 'Capture Photo';
      btnOpenCamRegister.onclick = null; // reset
    };
  });

  // Stop camera button (general)
  document.getElementById('btnStopCamera').addEventListener('click', ()=>{
    stopCamera(video);
    document.getElementById('btnStopCamera').classList.add('d-none');
  });

  // Register save
  document.getElementById('registerForm').addEventListener('submit', (e)=>{
    e.preventDefault();
    const name = document.getElementById('petName').value.trim();
    const breed = document.getElementById('petBreed').value.trim();
    const owner = document.getElementById('ownerName').value.trim();
    const photo = document.getElementById('photoData').value || '';
    if(!name||!breed||!owner){ alert('Please fill all fields'); return; }
    const pets = loadPets();
    pets.push({id: Date.now(), name, breed, owner, photo});
    savePets(pets);
    // reset form
    e.target.reset();
    document.getElementById('photoPreview').style.display='none';
    document.getElementById('photoData').value='';
    updateHome();
    showView('homeView');
  });

  // Camera controls for Scan
  document.getElementById('btnStartCamera').addEventListener('click', async ()=>{
    await startCamera(video);
    document.getElementById('btnStopCamera').classList.remove('d-none');
  });
  document.getElementById('btnStopCamera').addEventListener('click', ()=>{
    stopCamera(video);
    document.getElementById('btnStopCamera').classList.add('d-none');
  });

  // Simulate recognition: show last registered pet
  document.getElementById('btnSimulate').addEventListener('click', ()=>{
    const pets = loadPets();
    const last = pets.length? pets[pets.length-1] : null;
    displayPetProfile(last, document.getElementById('scanResult'));
  });
});
