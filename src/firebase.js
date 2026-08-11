import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyAil3clxr5vGlTNpC7qux7s8kUEt2mC-Fk",
  authDomain: "nexora-12728.firebaseapp.com",
  projectId: "nexora-12728",
  storageBucket: "nexora-12728.firebasestorage.app",
  messagingSenderId: "298898283968",
  appId: "1:298898283968:web:8a5e112c8e344f9a65fc25",
  measurementId: "G-13Q6V2C0FB"
};

const firebaseApp = initializeApp(firebaseConfig);

const database = getFirestore(firebaseApp);

export { database };