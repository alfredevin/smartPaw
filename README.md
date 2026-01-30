# Smart-Paw (Prototype)

Mobile-first SPA prototype for Smart-Paw — a Pet Identification System for Santa Cruz, Marinduque.

Features
- Bottom fixed navbar with Home / Scan / Register
- Register: save pet (name, breed, owner, captured photo) into `localStorage`
- Scan: camera preview and "Simulate Recognition" that loads the last registered pet

How to use
1. Open `index.html` in a mobile browser or desktop browser (preferably over HTTPS for camera access).
2. Use the **Register** tab to fill details and press **Capture Photo** to take a photo, then Save.
3. Use the **Scan** tab and press **Simulate Recognition** to display the last registered pet.

Notes
- Data is stored only in the browser's `localStorage` under key `smartPawPets`.
- Camera requires a secure context (https or localhost).
