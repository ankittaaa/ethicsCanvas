/*
****************
    GLOBALS       
****************
*/
var canvasPK;
var categories = [
    "Individuals Affected",
    "Groups Affected",
    "Behaviour",
    "Relations",
    "World Views",
    "Group Conflicts",
    "Product or Service Failure",
    "Problematic Use of Resources",
    "What can we do?",
    "Uncategorised"
];

var thisCanvas;
var ideas;
var comments;
var tags = [];
var taggedCanvasses;
var admins;
var users;
var publicCanvasses;
var privateCanvasses;
var selection;
var currentURL;
var tagButtons;

$j(document).ready(function(data){

    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    currentURL = window.location.pathname;
    var splitURL = currentURL.split("/");
    canvasPK = splitURL[splitURL.length - 2];
    var data = {
        "operation": "initialise"
    };

    // INITIAL AJAX REQUEST TO GET CANVAS INFORMATION AND RENDER IT TO PAGE
    // data = {
    //     "canvas_pk": canvasPK
    // };
    performAjaxGET(currentURL, data, initSuccessCallback, initFailureCallback);
});

/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/

    
$j(document).on("submit", ".idea-form", function(e){
/*
    Handler for editing of an idea, performs a POST and receives JSON response - this can be discarded as the text is already in the field 
    having been entered by user, and remains there on refresh

    Looks different to other event handlers as the elements it listens to are dynamically added 
*/
    e.preventDefault();
    inputText = escapeChars($j(this).find("input[value]")[0].value);
    // the $j(this).find() method doesn"t seem to work for idea_pk, which is a "list" attribute
    idea_pk = $j(this)[0][0].attributes[1].value;
    url = "/catalog/idea_detail/";

    data = {
        "input_text": inputText,
        "idea_pk": idea_pk
    };
    performAjaxPOST(url, data, editIdeaSuccessCallback, editIdeaFailureCallback);
});



$j(document).on("click", "#delete", function(e){
/*
    Handler for deleting an idea, performs a POST and receives JSON response 
    AND should remove the element from the DOM
*/
    e.preventDefault();
    idea_pk = $j(this)[0].attributes[1].value;

    url = "/catalog/delete_idea/";
    data = {
        "idea_pk": idea_pk
    };

    performAjaxPOST(url, data, deleteIdeaSuccessCallback, deleteIdeaFailureCallback);
    // delete list element with the matching list attribute
    $j("li[list = " + idea_pk + "]").remove();
});



$j(".new-idea").click(function(e){
/*
    Handler for addition of an idea, performs a POST and receives JSON response 
*/
    var category = $j(".new-idea").index(this);
    e.preventDefault();

    var url = "/catalog/new_idea/";
    var data = {
        "canvas_pk": canvasPK,
        "category": category
    };
    performAjaxPOST(url, data, newIdeaSuccessCallback, newIdeaFailureCallback);
});



$j(".new-tag").click(function(e){
/*
    Handler for addition of a tag
*/
    e.preventDefault();
    // url = "/catalog/canvas/" 
    data = {
        "canvas_pk": canvasPK,
        "operation": "add_tag",
        "tag": selection
    };
    performAjaxGET(currentURL, data, newTagSuccessCallback, newTagFailureCallback);
    selection = "";
});


$j(document).on("click", ".comments", function(e){
/*
    Handler for opening the comment thread for the clicked idea
*/
    idea_pk = this.attributes[1].value;
    url = "/catalog/comment_thread/" + idea_pk + "/";
    window.location.href = url;
});



$j("#collaborators").on("click", function(e){
    url = "/catalog/collaborators/" + canvasPK + "/";
    window.location.href = url;
});



$j(document).on("select", ".idea-form", function(e){
/*
    Function to maintain the most recently selected piece of text
    for use by the create-tag button
*/
    var start = e.target.selectionStart;
    var end = e.target.selectionEnd;
    var wholeString = e.target.value;

    selection = wholeString.substr(start, end-start);
    console.log(start);
    console.log(end);
    console.log(selection);
});

/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/

function newTagFailureCallback(data){
    console.log(data.responseText);
}

function deleteTagSuccessCallback(data){
    console.log(thisCanvas.fields.tags);
    var i = thisCanvas.fields.tags.indexOf(data);
    thisCanvas.fields.tags.splice(i, 1);
    console.log(thisCanvas.fields.tags);

}
function deleteTagFailureCallback(data){
    console.log(data.responseText);
}




function deleteIdeaSuccessCallback(data){
}

function deleteIdeaFailureCallback(data){
    console.log("Deletion Failed");
}

function newIdeaSuccessCallback(data){
/*
    Function to append a newly-created idea to the list of ideas
*/
    idea = JSON.parse(data);
    var listID = '#idea-list-' + idea[0].fields.category;

    $j(listID).append(
        "<li list = " + idea[0].pk +">                                                     \
            <form class = 'idea-form' action = ''>                                          \
                <input value = '' list = " + idea[0].pk + " placeholder = 'Add an idea'>    \
                <input type = 'submit' value = 'Submit'>                                    \
                <button id = 'delete' list = " + idea[0].pk + ">Delete Idea</button>        \
                <button class = 'comments' list = " + idea[0].pk + ">Comments</button>                                   \
            </form>                                                                         \
        </li>"
    );
}

function newIdeaFailureCallback(data){
    console.log(data);
}


function editIdeaSuccessCallback (data){
/* 
    Don't need to update anything, the text the user used to change the idea is
    still there thanks to the magic of AJAX (it will be rendered on refresh also)
*/ 
}

function editIdeaFailureCallback(data){
    console.log(data);
}

function initFailureCallback(data){
    console.log(data);
}

function commentSuccessCallback(data){
    console.log("comment thread opened");
}

function commentFailureCallback(data){
    console.log(data);
}
function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
    I'll do something with these eventually, for now just having them extracted is enough. Decisions on which may be global or which are useful 
    at all remain undecided. 
*/  
            ideas = JSON.parse(data.ideas);
            comments = JSON.parse(data.comments);
            tags = JSON.parse(data.tags);
            // console.log(tags);
            admins = JSON.parse(data.admins);
            users = JSON.parse(data.users);

            taggedCanvasses = new Array(tags.length);
            publicCanvasses = JSON.parse(data.public);
            privateCanvasses = JSON.parse(data.private);

            var allCanvasses = JSON.parse(data.allCanvasses);

            for (c in allCanvasses){
                if (allCanvasses[c].pk == canvasPK){
                    thisCanvas = allCanvasses[c];
                    break;
                }
            }

            populateTagList();
            populateIdeaList(); 

            tagButtons = new Vue({
                el: '#tag-div',
                data: {
                    tagList: tags,
                    canvasList: taggedCanvasses,
                    show: false,
                    showTag: true
                },
            })


}


function newTagSuccessCallback(data){
    // re-execute these steps so a new tag will, on being clicked, show it's in the current canvas
    tags = JSON.parse(data.tags);  
  
    taggedCanvasses = new Array(tags.length);
    publicCanvasses = JSON.parse(data.public);
    privateCanvasses = JSON.parse(data.private);
    var allCanvasses = JSON.parse(data.allCanvasses);

    for (c in privateCanvasses){
        console.log(privateCanvasses[c].fields.tags)
    }
    for (c in publicCanvasses){
        console.log(publicCanvasses[c].fields.tags)
    }
     
    populateTagList();
    // console.log(taggedCanvasses)

    // for (c in taggedCanvasses){
    //     if (taggedCanvasses[c].pk == canvasPK){
    //         var cc = taggedCanvasses[c];
    //         console.log(cc.fields.tags);
    //         break;
    //     }
    // }

    tagButtons.tagList = tags
    tagButtons.canvasList = taggedCanvasses
    console.log(tagButtons.tagList)
    console.log(tagButtons.canvasList)
}

/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/
function populateTagList(){
    var taggedPublic = [];
    var taggedPrivate = [];
    var tagged = [];

    for (var i = 0; i < tags.length; i++){

        // get a list of all public canvasses containing the current tag
        for (var j = 0; j < publicCanvasses.length; j++){
            if (publicCanvasses[j].fields.tags.includes(tags[i].pk)){
                taggedPublic.push(publicCanvasses[j]);
            }
        }

        // get a list of all private canvasses containing the current tag
        for (var j = 0; j < privateCanvasses.length; j++){
            if (privateCanvasses[j].fields.tags.includes(tags[i].pk)){
                taggedPrivate.push(privateCanvasses[j]);
            }
        }  

        tagged.push(taggedPublic);
        tagged.push(taggedPrivate);
        tagged = tagged[0].concat(tagged[1])

        taggedCanvasses[i] = tagged;

        taggedPublic = [];
        taggedPrivate = [];
        tagged = [];
    }
}

function populateIdeaList(){
/*
    Function to handle the initial population of the canvas by writing received data to the DOM
*/
    for (var i = 0; i < ideas.length; i++){
        if (ideas[i].fields.text){
            // only do string manipulation if there's a string to manipulate
            var ideaString = ideas[i].fields.text;
            ideaString = escapeChars(ideaString);
            var listID = "#idea-list-" + ideas[i].fields.category;

            $j(listID).append(
                "<li list = " + ideas[i].pk +">                                                     \
                    <form class = 'idea-form' action = ''>                                          \
                        <input value = '" + ideaString + "' list = " + ideas[i].pk +">    \
                        <input type = 'submit' value = 'Submit'>                                    \
                        <button id = 'delete' list = " + ideas[i].pk + ">Delete Idea</button>       \
                        <button class = 'comments' list = " + ideas[i].pk + ">Comments</button>                                   \
                    </form>                                                                         \
                </li>"
            );
        }

        else {  // add a placeholder to the end of the input's attributes so I can continue to reference 'list' in edit-idea as normal
            $j(listID).append(
                "<li list = " + ideas[i].pk +">                                                     \
                    <form class = 'idea-form' action = ''>                                          \
                        <input value = '' list = " + ideas[i].pk + " placeholder = 'Add an idea'>   \
                        <input type = 'submit' value = 'Submit'>                                    \
                        <button id = 'delete' list = " + ideas[i].pk + ">Delete Idea</button>       \
                        <button class = 'comments' list = " + ideas[i].pk + ">Comments</button>                                   \
                    </form>                                                                         \
                </li>"
            );
        }
    }
}





Vue.component('tag', {
    props: ['index', 'label'],
    delimiters:['<%', '%>'],

    data: function(){
        return {
            show: false,
            showTag: true,
            canvasList: taggedCanvasses,
            tagList: '',
        }
    },

    template: '#tag',

    // watcher for when the showTag data is changed by the emission of deleteTag by the 
    // tag-popup child element
    watch: {
        showTag: function(){
            var thisTag = tags[this.index]
            tags.splice(this.index, 1)
            data = {
                "tag_pk": thisTag.pk,
                "operation": "delete_tag"
            }
            performAjaxGET(currentURL, data, deleteTagSuccessCallback, deleteTagFailureCallback)
        },
        canvasList: function(){
            console.log(this.canvasList)
        }
    }
    ,
    created: function(){
        // console.log(this.canvasList[0][0].fields.title)
    },

    methods: {
        tagInfo: function(event, index){
        },  
        exitTagInfo: function(event){
            console.log('')
        }
    }
})




Vue.component('modal', {
  template: '#modal-template'
})





Vue.component('tag-popup', {
    props:['label', 'canvas'],
    delimiters: ['<%', '%>'],
    data: function(){
        return{
            canvasData: this.canvas,
            c: ''
        }
    },

    template:'<modal>\
                <div slot="header">\
                <h3><% label %></h3>\
                <h4>Appears in: </h4>\
                </div>\
                <ul slot="body">\
                    <li v-for="c in canvasData" style="list-style-type:none;">\
                        <a v-bind:href="url(c)" target="_blank">\
                            <% c.fields.title %>\
                        </a>\
                    </li>\
                </ul>\
                \
                <div slot=footer>\
                    <button class="delete-tag" @click="$emit(\'delete-tag\')">Delete</button>\
                    <button class="modal-default-button" @click="$emit(\'close\')">\
                    Close\
                    </button>\
                </div>\
            </modal>'
    ,

    computed: {
        titles: function(){
            var titles = []
            for( c in this.canvas ){
                titles.push(this.canvas[c].fields.title)
            }
            console.log(titles)
            return titles
        },
        keys: function(){
            var keys = []
            for( c in this.canvas ){
                keys.push(this.canvas[c].pk)
            }
            console.log(keys)
            return keys
        },
    },

    methods:{
        url: function(c){
            return "/catalog/canvas/" + c.pk
        },
        deleteTag: function(event){
            console.log(event.target)
            console.log(taggedCanvasses.indexOf(this.canvas))
        }
    }

})





function printMe(i){
    var str = 'Canvas tag is in: \n  '

    // console.log(taggedCanvasses.length)
    // for (var j = 0; j < taggedCanvasses[i].length; j++)
        // console.log(taggedCanvasses[i][j].fields.title)

    // new Vue({
    //         el: '#tag-div',
    //         data: {
    //             index: i
    //         }
    //     })
}



    


















































