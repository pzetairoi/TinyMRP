
function tiny3d(threefile) {

    // alert(threefile)

    // const scene = new THREE.Scene();
    // const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

    // const renderer = new THREE.WebGLRenderer();
    // renderer.setSize( window.innerWidth, window.innerHeight );
    // document.body.appendChild( renderer.domElement );

    // const geometry = new THREE.BoxGeometry();
    // const material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
    // const cube = new THREE.Mesh( geometry, material );
    // scene.add( cube );

    // camera.position.z = 5;

    // function animate() {
    //     requestAnimationFrame( animate );

    //     cube.rotation.x += 0.01;
    //     cube.rotation.y += 0.01;

    //     renderer.render( scene, camera );
    // };

    // animate();

    var scene, renderer, camera;
    var cube;
    var controls;
    
    init();
    animate();
    
    function init()
    {
        renderer = new THREE.WebGLRenderer( {antialias:true} );
        var width = window.innerWidth;
        var height = window.innerHeight;
        renderer.setSize (width, height);
        document.body.appendChild (renderer.domElement);
    
        scene = new THREE.Scene();
        
        var cubeGeometry = new THREE.BoxGeometry (10,10,10);
        var cubeMaterial = new THREE.MeshBasicMaterial ({color: 0x1ec876});
        cube = new THREE.Mesh (cubeGeometry, cubeMaterial);
    
        cube.position.set (0, 0, 0);
        scene.add (cube);
    
        camera = new THREE.PerspectiveCamera (45, width/height, 1, 10000);
        camera.position.y = 160;
        camera.position.z = 400;
        camera.lookAt (new THREE.Vector3(0,0,0));
    
        controls = new THREE.OrbitControls (camera, renderer.domElement);
        
        var gridXZ = new THREE.GridHelper(100, 10);
        gridXZ.setColors( new THREE.Color(0xff0000), new THREE.Color(0xffffff) );
        scene.add(gridXZ);
    
    }
    
    function animate()
    {
        controls.update();
        requestAnimationFrame ( animate );  
        renderer.render (scene, camera);
    }


}