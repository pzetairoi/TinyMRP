import * as THREE from '/static/js/three.js-master/build/three.module.js';
import { OrbitControls } from '/static/js/three.js-master/examples/jsm/controls/OrbitControls.js';
// import { ThreeMFLoader } from '/static/js/three.js-master/examples/jsm/loaders/3MFLoader.js';
import { ThreeMFLoader } from '/static/js/three.js-master/3MFLoader.js';

// Your Three.js initialization and rendering code here




let scene, camera, renderer;
console.log("teteltjlejel")

    function init() {
        console.log("in init")
        // Create the scene
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xdddddd);
        console.log("in init")
    
        // Set up the camera
        camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 1, 5000);
        camera.rotation.y = 45 / 180 * Math.PI;
        camera.position.x = 800;
        camera.position.y = 100;
        camera.position.z = 1000;
        console.log("before error in init")
    
        // Set up the renderer
        renderer = new THREE.WebGLRenderer({antialias: true});
        console.log("after error in init")
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        
    
        // Add controls
        let controls = new OrbitControls(camera, renderer.domElement);
        controls.addEventListener('change', function() {
            renderer.render(scene, camera);
        });
    
        // Add lighting
        let hlight = new THREE.AmbientLight(0x404040, 100);
        scene.add(hlight);
        let directionalLight = new THREE.DirectionalLight(0xffffff, 100);
        directionalLight.position.set(0, 1, 0);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        let light = new THREE.PointLight(0xc4c4c4, 10);
        light.position.set(0, 300, 500);
        scene.add(light);
        let light2 = new THREE.PointLight(0xc4c4c4, 10);
        light2.position.set(500, 100, 0);
        scene.add(light2);
        let light3 = new THREE.PointLight(0xc4c4c4, 10);
        light3.position.set(0, 100, -500);
        scene.add(light3);
        let light4 = new THREE.PointLight(0xc4c4c4, 10);
        light4.position.set(-500, 300, 500);
        scene.add(light4);
        console.log("before loading moadel")


        var loader = new ThreeMFLoader();
        loader.addExtension( ThreeMFLoader.MaterialsAndPropertiesExtension );
        loader.load( '/static/misc/test.3mf', function ( object3mf ) {

            scene.add( object3mf );
            animate(); 

        } );

    }
    


function animate() {
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}


console.log("before init")
init();
