/*
****************
    GLOBALS       
****************
*/
var canvasPK;
var projectPK;
var ethicsCategories = [
    "individuals-affected",
    "behaviour",
    "relations",
    "what-can-we-do",
    "world-views",
    "group-conflicts",
    "groups-affected",
    "product-or-service-failure",
    "problematic-use-of-resources",
    "uncategorised"
];

var businessCategories = [
    "key-partners",
    "key-activities",
    "key-resources",
    "value-propositions",
    "customer-relationships",
    "channels",
    "customer-segments",
    "cost-structure",
    "revenue-streams",
    "uncategorised"
];

var privacyCategories = [
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "TBD",
    "uncategorised"
];

var months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
];

var theCategories;

// sortedIdeas will become a 2d array of objects. the 'i' indices will be the categories, while the  
// 'j' indices will be an object encapulating an idea and an array of its comments ( { idea, comments[] } )

var sortedIdeas = new Array(10);
var typingBools = new Array(10);
var typingUser = new Array(10);


var thisCanvas;
var allTags = [];
var tags = [];
var taggedCanvases = [];
var allTaggedIdeas = [];
// var taggedIdeas;
var ideas;
var comments;

var users;
var admins;
var adminNames = [];
var activeUsers = [];
var loggedInUser
var isAuth;
var isAdmin;
var selection;
var currentURL;

var tagButtons;
var ideaListComponent;

var trialIdeaSocket;
var ideaSocket;
var commentSocket;
var tagSocket;
var collabSocket;


var typingEntered = false;
// initialise this variable as a timeout handle
var typingTimer = setInterval(
            function(){ console.log()}
            , 0);

window.clearTimeout(typingTimer);


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
        "operation": " "
    };

    // INITIAL AJAX REQUEST TO GET CANVAS INFORMATION AND RENDER IT TO PAGE
    performAjaxGET(currentURL, data, initSuccessCallback, initFailureCallback);
});

/*************************************************************************************************************
**************************************************************************************************************
                                        JQUERY EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/

$j(document).on("select", ".idea-input", function(e){
/*
    Function to maintain the most recently selected piece of text
    for use by the create-tag button
*/
    var start = e.target.selectionStart;
    var end = e.target.selectionEnd;
    var wholeString = e.target.value;

    selection = wholeString.substr(start, end-start);
});
/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/


/*************************************************************************************************************
                                            COLLABORATOR CALLBACKS
*************************************************************************************************************/
function addUserSuccessCallback(data){
    var tempUser = (JSON.parse(data.user));
    users.push(tempUser[0]);
}

function addUserFailureCallback(data){
    console.log(data.responseText);
}

function deleteUserSuccessCallback(data){
    var ui = JSON.parse(data.ui);
    var victimIsAdmin = JSON.parse(data.victimIsAdmin);

    if (users[ui].fields.username === loggedInUser[0].fields.username){
        alert("You've been removed from the project");
        // go back to project view after 2s 
        setInterval(
            function(){ 
                window.location.href="/catalog/project-list/"
            }, 
            100);
    }
    users.splice(ui, 1);
    /*
        Unlike the callback in projectDetail, we don't care if it's an admin as there are no
        admin-permission-required component operations in canvasDetail.
    */
}

function deleteUserFailureCallback(data){
    console.log(data);
}


function newActiveUserCallback(data){

    user = data.user;
    activeUsers.push(user[0].fields.username);


    collabSocket.send(JSON.stringify({
        'function': 'sendWholeList',
        'users': activeUsers,
    }));
}

function wholeListCallback(data){

    if (data.users.length <= activeUsers.length)
        return;
    else 
    {
        for (u in data.users){
            if (activeUsers.includes(data.users[u]))
                continue;
            else
                activeUsers.push(data.users[u]);
        }
    }
}

function removeActiveUserCallback(data){

    user = data.user;
    i = activeUsers.indexOf(user[0].fields.username);

    if (i > -1)
        activeUsers.splice(i, 1);
}


function promoteUserSuccessCallback(data){
    var tempAdmin = JSON.parse(data.admin);
    admins.push(tempAdmin[0]);
    adminNames.push(tempAdmin[0].fields.username);

    if (loggedInUser[0].fields.username === tempAdmin[0].fields.username)
    {
        isAdmin = true;
        ideaListComponent.admin = true;
    }
}

function promoteUserFailureCallback(data){
    // console.log(data.responseText);
}

function demoteAdminSuccessCallback(data){
    var ai = JSON.parse(data.ai);
    var victimName = adminNames[ai];
    admins.splice(ai, 1);
    adminNames.splice(ai, 1);

    if (loggedInUser[0].fields.username === victimName)
    {
        isAdmin = false;
        ideaListComponent.admin = false;
    }
}

function demoteAdminFailureCallback(data){
    console.log(data.responseText);
}

/*************************************************************************************************************
                                                IDEA CALLBACKS
*************************************************************************************************************/


function deleteIdeaSuccessCallback(data){
    var i = JSON.parse(data.i);
    var tempCategory = JSON.parse(data.category);
    var tempIdea = sortedIdeas[tempCategory][i].idea;

    // remove the victim {idea, [comments]} from the sorted ideas list
    sortedIdeas[tempCategory].splice(i, 1, {
        idea: null,
        comments: []
    });


    typingBools[tempCategory].splice(i, 1);
    typingUser[tempCategory].splice(i, 1);
}

function deleteIdeaFailureCallback(data){
    // console.log("Deletion Failed");
}

function newIdeaSuccessCallback(idea){
/*
    Function for updating the idea list for the modified category
    upon addition of new or deletion of current idea
*/

    var tempIdea = JSON.parse(idea);
    var tempCategory = tempIdea[0].fields.category;
    var newIdea = {
        idea: tempIdea[0],
        comments: []
    };

    // since ideas are sorted from newest to oldest, push the new idea to the front of sortedIdeas for the category
    // and an empty array for the comments, as a brand-new idea has no comments yet    
    if (sortedIdeas[tempCategory][0].idea === null)
    {
        // console.log(newIdea);
        // console.log(sortedIdeas[tempCategory][0]);
        sortedIdeas[tempCategory].splice(0, 1, newIdea);
        // console.log(sortedIdeas[tempCategory][0]);
    }
    else
    {
        sortedIdeas[tempCategory].unshift(newIdea);
    }   

    if (isAuth === true){
        typingBools[tempCategory].unshift(false);
        typingUser[tempCategory].unshift('');
    }    

}

function newIdeaFailureCallback(data){
    // console.log(data);
}


function editIdeaSuccessCallback (data){
    var inIdea = (JSON.parse(data.idea))[0];
    var tempCategory = inIdea.fields.category;

    var i = JSON.parse(data.i);
    var oldText = escapeHTMLChars(data.oldText);
    sortIdeas(inIdea, i, tempCategory, oldText);
    var tempTag;
    // check for adding new
    for (tag in allTags){
        // if the new idea string contains a tag declared in a different canvas
        tempTag = allTags[tag];

        if (inIdea.fields.text.includes(tempTag.fields.label) && (oldText.includes(tempTag.fields.label) === false)){
            // add that tag to the current canvas's list IF IT DOES NOT EXIST

            tagSocket.send(JSON.stringify({
                    'function': 'addTag',
                    "label": tempTag.fields.label,
                    "canvas_pk": canvasPK,
            }));
        }
    }
    // check for removing old
    for (tag in tags){
        tempTag = allTags[tag];

        if (oldText.includes(tempTag.fields.label) && (inIdea.fields.text.includes(tempTag.fields.label) === false)){
            // TODO: CHECK THE OTHER IDEAS!!!

            // remove the tag and the tag's details entirely    
            tagSocket.send(JSON.stringify({
                    'function': 'removeTag',
                    "idea_pk": inIdea.pk,
                    "label": tempTag.fields.label,
                    "canvas_pk": canvasPK,
            }));
        }
    }
}

function editIdeaFailureCallback(data){
    // console.log(data);
}


function typingCallback(data, f){
    // // console.log(f);
    var tempCategory = data['category'];
    var tempName = data['username'];
    var i = data['i']
    // // console.log("category: " + tempCategory);
    // // console.log("idea: " + i);
    // do nothing, the logged in user knows when they're typing
    if (tempName == loggedInUser[0].fields.username)
        return;

    if (f === "typing"){
        // // console.log(typingBools[tempCategory]);
        typingUser[tempCategory].splice(i, 1, tempName);
        typingBools[tempCategory].splice(i, 1, true);
        // // console.log(typingBools[tempCategory]);
    }
    else {
        // // console.log(typingBools[tempCategory]);
        typingUser[tempCategory].splice(i, 1, '');
        typingBools[tempCategory].splice(i, 1, false);
        // // console.log(typingBools[tempCategory]);
    }



}
/*************************************************************************************************************
                                        COMMENT CALLBACKS
*************************************************************************************************************/


function addCommentSuccessCallback(data){
    var i = JSON.parse(data.i);
    var returnComment = JSON.parse(data.comment);
    var tempCategory = JSON.parse(data.category);
    sortedIdeas[tempCategory][i].comments.unshift(returnComment[0]);
}

function addCommentFailureCallback(data){
    console.log(data);
}


function deleteCommentSuccessCallback(data){
    // var parsedData = JSON.parse(data);
    var i = JSON.parse(data.i);
    var c = JSON.parse(data.c);
    var tempCategory = JSON.parse(data.category);

    sortedIdeas[tempCategory][i].comments.splice(c, 1);
}

function deleteCommentFailureCallback(data){
    console.log(data);
}

function resolveIndividualCommentSuccessCallback(data){
    var i = JSON.parse(data.i);
    var c = JSON.parse(data.c);
    var tempCategory = JSON.parse(data.category);

    var tempComment = sortedIdeas[tempCategory][i].comments[c];

    tempComment.fields.resolved = true;
    sortedIdeas[tempCategory][i].comments.splice(c, 1, tempComment);
}

function resolveIndividualCommentFailureCallback(data){
    console.log(data);
}

function resolveAllCommentsSuccessCallback(data){
    var tempCategory = JSON.parse(data.category);
    var i = JSON.parse(data.i);

    // empty the comments for the idea
    var length = sortedIdeas[tempCategory][i].comments.length;
    var tempComment;

    for (var c = 0; c < length; c++)
    {
        tempComment = sortedIdeas[tempCategory][i].comments[c];
        tempComment.fields.resolved = true;
        sortedIdeas[tempCategory][i].comments.splice(c, 1, tempComment);
    }
}
function resolveAllCommentsFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                            TAG CALLBACKS
*************************************************************************************************************/

function newTagSuccessCallback(data){
    // re-execute these steps so a new tag will, on being clicked, show it's in the current canvas
    var newTags = JSON.parse(data.tags);
    var tempTaggedCanvases = [];
    var tempTaggedIdeas = [];

    for (i in newTags){
        tempTaggedCanvases.push(JSON.parse(data.taggedCanvases[i]));
        tempTaggedIdeas.push(JSON.parse(data.taggedIdeas[i]));
    }

    // console.log(newTags.length);
    // console.log(tempTaggedCanvases.length);
    // console.log(tempTaggedIdeas.length);
    // for (i in newTags){
    //     for (j in tempTaggedCanvases){
    //         console.log(tempTaggedCanvases[i][j]);
    //         console.log(tempTaggedIdeas[i][j]);
    //     }
    // }
    // for (i in newTags){
    //     for (j in tempTaggedIdeas){
    //         console.log("TAG: " + newTags[i].fields.label);
    //         console.log(tempTaggedIdeas[i][j].pk);
    //     }
    // }

    for (i in newTags){
        var tagExists = false;
        var canvasTagged = false;
        
        for (t in tags){
            if (tags[t].pk == newTags[i].pk){
                tagExists = true;
                break;
            }
        }
        for (j in tempTaggedCanvases[i]){
            if (tempTaggedCanvases[i][j].pk == canvasPK){
                canvasTagged = true;
                break;
            }
        }


            // console.log("is in?" + (tempTaggedCanvases[i][j].pk == canvasPK));
            // if the tag doesn't exist, but the canvas is tagged by it, add it
            if (tagExists === false && canvasTagged === true){
                if (tags[0].pk !== null){
                    tags.push(newTags[i]);
                    taggedCanvases.push(tempTaggedCanvases[i]);
                    allTaggedIdeas.push(tempTaggedIdeas[i]);
                }
                else {
                    tags.splice(0, 1, newTags[i]);
                    taggedCanvases.splice(0, 1, tempTaggedCanvases[i]);
                    allTaggedIdeas.splice(0, 1, tempTaggedIdeas[i]);
                }
                break;
            }
            // if the tag DOES exist and the canvas is tagged by it, update it
            else if (tagExists === true && canvasTagged === true){
                console.log("UPDATING...");
                // console.log(allTaggedIdeas);
                // console.log(allTaggedIdeas[i]);
                // console.log(tempTaggedIdeas[i]);
                taggedCanvases.splice(i, 1, tempTaggedCanvases[i]);
                allTaggedIdeas.splice(i, 1, tempTaggedIdeas[i]);
            }

        // otherwise do nothing
    }
}

function newTagFailureCallback(data){
    console.log(data.responseText);
}


function removeTagSuccessCallback(data){
    // differs to deleteTag in that it is called when a tag's occurrences in a canvas are altered. 
    // the tag's presence may still be in that canvas and in other canvases, so it shouldn't be deleted.
    // instead the set of ideas is altered.
    var victimTag = JSON.parse(data.tag)[0];
    var tempTaggedCanvases = [];
    var tempTaggedIdeas = [];

    // for (i in newTags){
    tempTaggedCanvases = (JSON.parse(data.taggedCanvases));
    tempTaggedIdeas = (JSON.parse(data.taggedIdeas));
    // }

    var tagExists = false;
    var canvasTagged = false;
    var tagIndex = -1;

    for (i in tags){
        if (tags[i].pk == victimTag.pk){
            tagExists = true;
            tagIndex = i;
        }
        for (j in tempTaggedCanvases){
            if (tempTaggedCanvases[j].pk == canvasPK){            
                canvasTagged = true;
            }
        }
    }



    // if the tag does exist, but the canvas is not tagged by it, remove it
    if (tagExists === true && canvasTagged === false){
        if (tags.length > 0 && tags.length != 1){
            // simply remove the tag if there will be more remaining
            tags.splice(tagIndex, 1);
            taggedCanvases.splice(tagIndex, 1);
            allTaggedIdeas.splice(tagIndex, 1);
        }
        else {
            // if removing last tag, replace with null tag
            var tempTag = tags[i];
            tempTag.pk = null;
            tempTag.fields.date_created = null;
            tempTag.fields.date_modified = null;
            tempTag.fields.label = null;
            tags.splice(i, 1, tempTag);
            taggedCanvases.splice(0, 1);
            allTaggedIdeas.splice(0, 1);
        }
        return;
    }
    // if the tag does exist and the canvas is tagged by it, update it to reflect removal form other canvases
    else if (tagExists === true && canvasTagged === true){
        taggedCanvases.splice(tagIndex, 1, tempTaggedCanvases);
        allTaggedIdeas.splice(tagIndex, 1, tempTaggedIdeas);

    }

        // otherwise do nothing

}


function deleteTagSuccessCallback(data){
    console.log("hello");

    var tag = JSON.parse(data.tag)[0];
    console.log(tag);
    console.log(tags);
    var i; 

    for (t in tags){
        if (tags[t].pk == tag.pk){
            i = t; 
            break;
        }
    }

    if (i > -1){
        if (tags.length > 1){ 
            // if there'll be more tags left, just delete it
            tags.splice(i, 1);
            taggedCanvases.splice(i, 1);
            allTaggedIdeas.splice(i, 1);
        }
        else {
            // if last tag, replace with null tag
            var tempTag = tags[i];
            tempTag.pk = null;
            tempTag.fields.date_created = null;
            tempTag.fields.date_modified = null;
            tempTag.fields.label = null;
            tags.splice(i, 1, tempTag);
            taggedCanvases.splice(0, 1);
            allTaggedIdeas.splice(0, 1);
        }
    }


}

function deleteTagFailureCallback(data){
}


/*************************************************************************************************************
                                            INITIAL CALLBACK
*************************************************************************************************************/


function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
    I'll do something with these eventually, for now just having them extracted is enough. Decisions on which may be global or which are useful 
    at all remain undecided. 
*/  
    // initially declare empty arrays for each index of sortedIdeas
    for (var i = 0; i < sortedIdeas.length; i++){
        sortedIdeas[i] = new Array();
        typingBools[i] = new Array();
        typingUser[i] = new Array();
    }

    comments = JSON.parse(data.comments);
    ideas = JSON.parse(data.ideas);
    
    allTags = JSON.parse(data.allTags);
    loggedInUser = JSON.parse(data.loggedInUser);
    projectPK = JSON.parse(data.projectPK);
    thisCanvas = JSON.parse(data.thisCanvas)[0];
    canvasType = thisCanvas.fields.canvas_type;
    users = JSON.parse(data.users);

    admins = JSON.parse(data.admins);

    for (a in admins)
        adminNames.push(admins[a].fields.username);

        if (adminNames.indexOf(loggedInUser[0].fields.username) !== -1)
            isAdmin = true;
        else
            isAdmin = false;


    if (loggedInUser.length === 0)
        isAuth = false;
    
    if (loggedInUser.length > 0) {
        isAuth = true;
        initialiseSockets();
    }

    // initialise each category as empty


    if (ideas.length > 0){
        for (idea in ideas){
            var ideaComments = [];
            for (comment in comments){
                if (comments[comment].fields.idea === ideas[idea].pk){
                    ideaComments.push(comments[comment]);
                }
            }

            sortedIdeas[ideas[idea].fields.category].splice(idea, 1, {
                idea: ideas[idea],
                comments: ideaComments
            });
            typingBools[ideas[idea].fields.category].push(false);
            typingUser[ideas[idea].fields.category].push('');
        }
    }

    for (s in sortedIdeas){
        if (sortedIdeas[s].length === 0){
            sortedIdeas[s].push({
                idea: null,
                comments: []
            });
            typingBools[s].push(false);
            typingUser[s].push('');
        }
    }




    if (isAuth === true){
        $j('#canvas-title').html(thisCanvas.fields.title);
        newTags = JSON.parse(data.tags);

        if (newTags[0].pk !== null){
            for (t in newTags){
                tags.push((newTags[t]));
                allTaggedIdeas.push(JSON.parse(data.allTaggedIdeas[t]));
                taggedCanvases.push(JSON.parse(data.taggedCanvases[t]));
            }
        }
        else {
            tags.push(newTags[0]);
            allTaggedIdeas = [];
            taggedCanvases = [];
        }
    }
    else {
        $j('#canvas-title').html("Trial Canvas");

        // only want to initialise the ideaSocket so that new idea JSON objects can be acquired - NOT ADDED TO A CANVAS
        trialIdeaSocket = new WebSocket(
            'ws://' + window.location.host + 
            '/ws/canvas/' + canvasPK + '/trial-idea/'
        );

        trialIdeaSocket.onmessage = function(e){
            // // console.log("Received");
            var data = JSON.parse(e.data);
            var idea = data['idea'];
            newIdeaSuccessCallback(idea);
        };
    }

    console.log(allTaggedIdeas);
    if (canvasType === 0)
        theCategories = ethicsCategories;
    else if (canvasType === 1)
        theCategories = businessCategories;
    else if (canvasType === 2)
        theCategories = privacyCategories;


    ideaListComponent = new Vue({
        el: '#idea-div',
        data: {
            ideaList: sortedIdeas,
            categories: theCategories,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
            adminNameList: adminNames,
        }
    })


    if (isAuth === true){
        tagButtons = new Vue({
            el: '#tag-div',
            data: {
                tagList: tags,
                canvasList: taggedCanvases,
                ideaList: allTaggedIdeas,
                show: false,
                auth: isAuth,
            },
        })    
    }
}

function initFailureCallback(data){
    // console.log(data);
}

/*************************************************************************************************************
**************************************************************************************************************
                                            VUE COMPONENTS
**************************************************************************************************************   
**************************************************************************************************************/

/*************************************************************************************************************
                                            IDEA-LIST COMPONENT
*************************************************************************************************************/


Vue.component('idea-list', {
    props: [],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            ideaList: sortedIdeas,
            categories: theCategories,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
            adminNameList: adminNames,
        }
    },

    template:'#ideas',

    watch: {
    },
    
    methods: {

    },
    created: function(){
    }
})

/*************************************************************************************************************
                                            IDEA-ELEM COMPONENT
*************************************************************************************************************/
 
Vue.component('idea', {
    props: ['user', 'is-typing', 'ideas', 'index', 'categories', 'is-auth', 'admin-names'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            showComments: false,
            // Array of booleans for displaying individual modal components. As a single boolean, all modals will be rendered instead of the one for the comment thread of the clicked idea. 
            showCommentThread: new Array(this.ideas.length),
            isTypingBools: this.isTyping,
            typingUser: this.user,
            categoryList: this.categories,
        }
    },
    
    template:`  <div v-bind:class="this.flexClass">     
                    <h3><% title() %></h3> 
                     
                    <div class="idea-container" v-if="escapedIdeas[0]" > 
                        <div v-for="(idea, i) in escapedIdeas"> 
                             
                            <div v-bind:id=textID(i)> 
                                <textarea class="idea-input"  
                                    type="text" :value="idea.fields.text" 
                                    @blur="changed($event, idea, i)" 
                                    @keydown="keydownCallback($event, idea, i)"  
                                    @keypress="setTyping($event, idea, i)" 
                                    @paste="setTyping($event, idea, i)" 
                                    placeholder="Enter an idea"/> 
                                    <p id="user-typing" v-show="isTypingBools[i] == true">
                                        <%typingUser[i]%> is typing...
                                    </p> 
                            </div> 
                            
                            <div class='idea-buttons'> 
                                <button id="delete-idea" class="delete" @click="deleteIdea($event, idea, i)" title="delete">X</button> 
                                <button v-if="isAuth" id="comment-button" v-on:click="displayMe(i)"> 
                                    <span>Comments (<% commentList[i].length %>)</span> 
                                </button> 
                                <button v-else id="comment-button" title="Sign up to use this feature" disabled> 
                                    <span>Comments</span> 
                                </button> 
                                <comment v-show=showCommentThread[i] v-bind:commentList="commentList[i]" v-bind:idea="idea" v-bind:i="i" v-bind:admins="adminNameList" @close="displayMe(i)"> 
                                </comment> 
                            </div> 
                        </div> 
                    </div> 
                    <div class="main-idea-buttons"> 
                        <button id="new-idea-button" @click="newIdea($event)">+</button> 
                        <button v-if="escapedIdeas[0]" id="new-tag-button" v-on:click="newTag()">Tag Selected Term</button> 
                    </div>  
                </div>
    `,
         
    computed: {
         adminNameList: function(){
            return this.adminNames
        },

        flexClass: function(){
            var i = this.index
            return "idea-flex-container-" + i
        },

        category: function(){
            return ethicsCategories[this.index]
        },

        ideaList: {
            get: function(){
                // // console.log(this.ideas[0])
                var list = []

                
                // if (this.ideas[0] !== null){
                    if (this.ideas[0] !== null){
                        for (i in this.ideas){
                            list.push(this.ideas[i].idea)
                        }
                    }
                // }
                return list
            },

            set: function(ideasInput){
                var list = []
                if (this.ideasInput !== null){
                    for (i in this.ideasInput){
                        list.push(this.ideasInput[i].idea)
                    }
                }
                return list
            },
        },

        commentList: {
            get: function(){
                var list = []
                if (isAuth === true && this.ideas[0] !== null){
                    if (this.ideas[0].idea !== null){
                        for (i in this.ideas){
                            list.push(this.ideas[i].comments)
                        }
                    }
                }
                return list
            }
        },
        /* 
            using a computed property to escape the html characters such as &apos as vue throws an 
            "invalid assignment left-hand side" error when I call the method directly with v-model, 
            the error not appearing until @change is triggered   
        */ 
        escapedIdeas: function(){
            var escaped = this.ideaList


            for (idea in escaped){
                if (escaped[idea] == null)
                    continue
                escaped[idea].fields.text = this.ideaString(escaped[idea])
            }
            return escaped
            
        },
    },

    methods: {

        textID: function(i){
            return "category-"+this.index+"-idea-"+i
        },   

        displayMe(i){
        /*
            For setting an individual truth value to display a single modal component's comment thread, or to close it.
            This method is required as Vue doesn't detect array changes normally. 
        */
            Vue.set(this.showCommentThread, i, !this.showCommentThread[i])
        },

        currentIdeaComments(idea, comments){

            var returnComments = []
            if (isAuth === true){
                for (c in comments){
                    if (comments[c].fields.idea === idea.pk)
                    {   
                        returnComments.push(comments[c])
                    }
                }
            return returnComments
            }
        },

        close: function(){
            this.showCommentThread = false
        },

        displayComments: function(event, idea){
            // // console.log(idea)
        },

        title: function(){
            var cat = this.categoryList[this.index]
            var newCat = []
            var returnCat = ''

            cat = cat.split('-')

            for (c in cat){
                var upperCat = cat[c][0].toUpperCase()
                returnCat += upperCat + cat[c].slice(1, cat[c].length) + ' '
            }

            return returnCat
        },

        ideaString: function(idea){
            var string = escapeChars(idea.fields.text)
            // the following is to convert elements like &apos back to " ' " 
            var scratch = document.createElement("textarea")
            scratch.innerHTML = string

            return scratch.value
        },
        newIdea(event){

            if (isAuth === true)
            {
                ideaSocket.send(JSON.stringify({
                    'function': 'addIdea',
                    'category': this.index,
                }));
            }
            else {
                trialIdeaSocket.send(JSON.stringify({
                    // 'function': 'addIdeaTrial',
                    'category': this.index,
                }));
            }
        },

        deleteIdea(event, idea, i){
            if (isAuth === true){
                // CALL removeTag BEFORE DELETING - VIEW FUNCTION NEEDS THE IDEA TO EXIST
                for (t in tags){
                    if (idea.fields.text.includes(tags[t].fields.label)){
                        tagSocket.send(JSON.stringify({
                            'function': 'removeTag',
                            "idea_pk": idea.pk,
                            "label": tags[t].fields.label,
                            "canvas_pk": canvasPK,
                        }));
                    }
                    console.log(tags[t].fields.label + " removed.");
                }

                ideaSocket.send(JSON.stringify({
                    'function': 'deleteIdea',
                    'idea_pk': idea.pk,
                    'i': i
                }));
            }
            else
                sortedIdeas[this.index].splice(i, 1)
        },

        changed(event, idea, i){
            var text = escapeChars(event.target.value)
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()

            if (isAuth === true){
                window.clearTimeout(typingTimer)
                
                ideaSocket.send(JSON.stringify({
                    'function': 'modifyIdea',
                    'input_text': text,
                    'idea_pk': idea.pk,
                    'category': this.index,
                    'i': i

                }));
                // if a user entered loads of whitespace, then replace current input field with trimmed text
                event.target.value = text
                idea.fields.text = text
                event.target.blur()
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, i: i, index: this.index})
                    , 0
                )
            }
            else {
                currIdea = sortedIdeas[this.index][i].idea
                currIdea.fields.text = text

                if (sortedIdeas[this.index].length > 1){
                    sortIdeas(currIdea, i, this.index, "")
                }
                else{
                    sortedIdeas[this.index].splice(i, 1, {
                        idea: currIdea,
                        comments: []
                    })
                }

            }

        },

        keydownCallback(event, idea, i){
            key = event.key
            
            if (key == "Enter")
                event.target.blur()

            if (key == "Escape")
                this.ideaList[i].fields.text = this.ideaList[i].fields.text
        },

        setTyping(event, idea, i){
            if (isAuth === true){

                window.clearTimeout(typingTimer)

                // only want to send something down the socket the first time this function is called
                if (typingEntered == false){        
                    ideaSocket.send(JSON.stringify({
                        'function': 'typing',
                        'category': this.index,
                        'username': loggedInUser[0].fields.username,
                        'i': i
                    }))
                }

                typingEntered = true

                // timeout function for clearing the <user> is typing message on other windows - waits 2s 
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, i: i, index: this.index})
                    , 2000
                )
            }
        },

        newTag(){
            if (isAuth === true){
                tagSocket.send(JSON.stringify({
                    'function': 'addTag',
                    "label": selection,
                    "canvas_pk": canvasPK,
                }));
                selection = ""
            }
        }

    },

    watch: {
    },   

    created: function(){
        for (var i = 0; i < this.showCommentThread.length; i++){
            this.showCommentThread[i] = false
        }
    },
})

/*************************************************************************************************************
                                            COMMENT COMPONENT
*************************************************************************************************************/
 
Vue.component('comment', {
    props: ['comment-list', 'show-comments', 'idea', 'i', 'admins'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            comments: this.commentList,
        }
    },
    
    template:`
                <modal v-show="show"> 
                 
                 
                    <div slot="header"> 
                        <h3>Comments</h3> 
                        <input value="" placeholder = "Type a comment" @change="newComment($event)"> 
                        <button>Post</button> 
                    </div> 
                 
                 
                    <div slot="body"> 
                        <ul> 
                            <li v-for="(comment, c) in commentList"> 
                                <div class="comment-elem" v-if="comment.fields.resolved == false">
                                    <% comment.fields.text %> 
                                    </br> 
                                    <% commentAuthorString(comment) %>
                                    <div v-show="isAdmin">
                                        <button class="delete-comment" @click="deleteComment($event, comment, c)" title="delete">Delete</button> 
                                        <button class="resolve-individual-comment" @click="resolveIndividualComment($event, comment, c)" title="delete">Resolve</button> 
                                    </div>
                                </div>
                                <div class="comment-elem resolved" v-else>
                                    <% comment.fields.text %> <strong> <% " (RESOLVED)" %> </strong>
                                    </br> 
                                    <% commentAuthorString(comment) %>
                                    <button v-show="isAdmin" class="delete-comment" @click="deleteComment($event, comment, c)" title="delete">Delete</button>
                                </div>
                            </li> 
                        </ul> 
                    </div> 

                    <div class='comment-footer' slot="footer">
                        <button v-show="isAdmin" class="resolve-comments" @click="resolveAllComments(idea)">Resolve All Comments</button>
                        <button class="modal-default-button" @click="$emit('close')">Close</button>
                    </div>
                </modal>`
,
         
    computed: {
        currentIdea: function(){
            return this.idea
        },
        show: function(){
            return this.showComments
        },
        selfIndex: function(){
            return this.i
        },
        adminNames: function(){
            return this.admins 
        },
        isAdmin: function(){
            return (this.adminNames.includes(loggedInUser[0].fields.username))
        },
    },
    
    watch: {
        adminNames: function(){
            console.log("hi")
        }
    },   

    methods: {
        

        commentAuthorString: function(comment){

            var str = "\n By " 
                + this.getCommentAuthor(comment) 
                + " at " 
                + this.getHumanReadableTimestamp(comment.fields.timestamp)

            return str
        },

        newComment(event){
            var text = escapeChars(event.target.value)
            event.target.value = ''
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()
            
            commentSocket.send(JSON.stringify({
                'function': 'addComment',
                'input_text': text,
                'i': this.selfIndex,
                'idea_pk': this.currentIdea.pk
            }));
        },

        deleteComment(event, comment, c){
            commentSocket.send(JSON.stringify({
                'function': 'deleteComment',
                "comment_pk": comment.pk,
                'i': this.selfIndex,
                'c': c
            }));
        },

        resolveIndividualComment(event, comment, c){
            commentSocket.send(JSON.stringify({
                'function': 'resolveIndividualComment',
                "comment_pk": comment.pk,
                'i': this.selfIndex,
                'c': c
            }));
        },

        resolveAllComments(idea){
            commentSocket.send(JSON.stringify({
                'function': 'resolveAllComments',
                "idea_pk": this.currentIdea.pk,
                'i': this.selfIndex,
            }));
        },

        getCommentAuthor(comment){
            userPK = comment.fields.user 
            
            for (u in users){
                if (users[u].pk === userPK)
                    return users[u].fields.username
            }
            return "Unknown"
        },

        getHumanReadableTimestamp(timestamp){
            var time = timestamp
            var splitOne = time.split('T')
            var year = splitOne[0]
            var time = splitOne[1].split('.')[0]

            var splitYear = year.split('-')

            var day = splitYear[2]
            var month = months[parseInt(splitYear[1]) - 1]
            year = splitYear[0]

            return(day + " " + month + " " + year + " at " + time)
        }
    },
    created: function(){
        // // console.log(this.comments.length)
        // for (a in this.admins) {

        //     console.log(this.admins[a])
        // }
    }
})

/*************************************************************************************************************
                                            TAG-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('tag', {
    props: ['index', 'label'],
    delimiters:['<%', '%>'],
    template: '#tag',

    data: function(){
        return {
            show: false,
            showTag: true,
            canvasList: taggedCanvases,
            tagList: tags,
            auth: isAuth,
            ideaList: allTaggedIdeas,
        }
    },



    // watcher for when the showTag data is changed by the emission of deleteTag by the 
    // tag-popup child element
    watch: {
        showTag: function(){
            var thisTag = tags[this.index]
            tags.splice(this.index, 1)
        },
        canvasList: function(){
            // // console.log(this.canvasList)
        }
    },

    methods: {
        tagInfo: function(event, index){
        },  
        exitTagInfo: function(event){
            // // console.log('')
        }
    }
})

/*************************************************************************************************************
                                            TAG-ELEM COMPONENT
*************************************************************************************************************/
 
Vue.component('tag-popup', {
    props:['tag', 'label', 'canvases', 'index', 'ideas'],
    delimiters: ['<%', '%>'],
    data: function(){
        return {
            c: '',
            selfTag: this.tag,
            ideaList: this.ideas,
            canvasData: this.canvases,
        }
    },

    template:
        `   
            <modal>
                <div slot="header">
                <h3><% label %></h3>
                <h4>Appears in: </h4>
                </div>
                <ul slot="body">
                    <li v-for="c in this.canvases" style="list-style-type:none;">
                        <a v-bind:href="url(c)" target="_blank">
                            <% tagLink(c) %>
                        </a>
                    </li>
                </ul>
                
                <div slot="footer">
                    <button class="delete-tag" @click="deleteTag($event)">Delete</button>
                    <button class="modal-default-button" @click="$emit('close')">
                    Close
                    </button>
                </div>
            </modal>
        `
    ,

    computed: {
        // canvasData: function(){
        //     return this.canvases
        // },
        // ideaList: function(){
        //     return this.ideas
        // },
        // selfTag: function(){
        //     return this.tag
        // }


    },

    watch: { 
        ideaList: function(){
            // console.log(this.tag.label)
            for (i in this.ideaList){
                    console.log(this.ideas[i].pk)
            }
            console.log("******")
        }
    },

    methods:{
        url: function(c){

            return "/catalog/canvas/" + c.pk
        },

        tagLink: function(c){
            var ideaString = 'Ideas: '

            for (i in this.ideaList){
                if (this.ideaList[i].fields.canvas === c.pk){
                        ideaString += this.ideaList[i].pk + ', '
                }
            }
            ideaString = ideaString.slice(0, ideaString.length - 2)

            return c.fields.title + " " + ideaString

        },
        deleteTag: function(event){
            tagSocket.send(JSON.stringify({
                'function': 'deleteTag',
                'label': this.tag.fields.label,
                'canvas_pk': canvasPK,
            }));
        }
    },
    created: function(){
        console.log(this.selfTag.pk)
        console.log(this.label)
    }

})

/*************************************************************************************************************
                                            MODAL COMPONENT
*************************************************************************************************************/
 
Vue.component('modal', {
  template: '#modal-template'
})

/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/

function initialiseSockets(){

/********************************************************************
*********************************************************************
                        SOCKET DECLARATIONS
*********************************************************************                            
*********************************************************************/

    ideaSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/idea/'
    );

    commentSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/comment/'
    );


    tagSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/project/' + projectPK + '/tag/'
    );


    collabSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/project/' + projectPK + '/collab/'
    );
/********************************************************************
*********************************************************************
                            CALLBACKS
*********************************************************************                            
*********************************************************************/
    
    /***********************************
                IDEA SOCKET
    ************************************/
    ideaSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];
        
        if (f.includes("typing")) {
            typingCallback(data, f);
            return;
        }
        switch(f) {
            case "modifyIdea": {
                editIdeaSuccessCallback(data);
                break;
            }
            case "addIdea": {
                var idea = data['idea'];
                newIdeaSuccessCallback(idea);
                break;
            }
            case "deleteIdea": {
                deleteIdeaSuccessCallback(data);
                break;
            }
        }
    };

    /***********************************
                COMMENT SOCKET
    ************************************/
    commentSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "addComment": {
                addCommentSuccessCallback(data);
                break;
            }
            case "deleteComment": {
                deleteCommentSuccessCallback(data);
                break;
            }
            case "resolveIndividualComment": {
                resolveIndividualCommentSuccessCallback(data);
                break;
            }
            case "resolveAllComments": {
                resolveAllCommentsSuccessCallback(data);
                break;
            }
        }
    };

    /***********************************
                TAG SOCKET
    ************************************/
    tagSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];
        // console.log(e.data);
        // console.log(data);

        switch(f) {
            case "addTag": {
                newTagSuccessCallback(data.data);
                break;
            }
            case "removeTag": {
                removeTagSuccessCallback(data.data);
                break;
            }
            case "deleteTag": {
                deleteTagSuccessCallback(data.data);
                break;
            }
        }
    };


    /***********************************
                COLLAB SOCKET
    ************************************/
    collabSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "promoteUser": {
                promoteUserSuccessCallback(data);
                break;
            }
            case "demoteUser": {
                demoteAdminSuccessCallback(data);
                break;
            }
            case "addUser": {
                addUserSuccessCallback(data);
                break;
            }
            case "deleteUser": {
                deleteUserSuccessCallback(data);
                break;
            }
            case "newActiveUser": {
                newActiveUserCallback(data);
                break;
            }

            case "removeActiveUser": {
                removeActiveUserCallback(data);
                break;
            }

            case "sendWholeList": {
                wholeListCallback(data);
                break;
            }
        }
    };

    collabSocket.onopen = function(e){
        collabSocket.send(JSON.stringify({
            "function": "newActiveUser",
            "user": loggedInUser,
        }));
    };
}

function escapeHTMLChars(text){

    var string = escapeChars(text)
    // the following is to convert elements like &apos back to " ' " 
    var scratch = document.createElement("textarea")
    scratch.innerHTML = string
    return scratch.value
}

function setFalse(){
    this.isTyping = false;

    ideaSocket.send(JSON.stringify({
        'function': 'done_typing',
        'category': this.index,
        'username': loggedInUser[0].fields.username,
        'i': this.i

    }))
    window.clearTimeout(typingTimer)
    typingEntered = false;
}   


function sortIdeas(inIdea, i, tempCategory, oldText){
    /*
        Function called when an idea has been modified, to move the idea and its attached comments to the top of the list,
        where it would be if the page was refreshed. Also checks if any tag occurrences have been removed by checking if the substring
        equal to any tag label existed in the previous idea text field and now no longer occurs
    */
    var prevIdea = inIdea;
    var currentIdea = sortedIdeas[tempCategory][i].idea;
    
    if (isAuth === true){
        for (t in tags){
            // iterate through tags, check for occurrences in old text that no longer exist in new text
            var tempIdeaText = currentIdea.fields.text;

            if ((oldText.includes(tags[t].fields.label) === true) && (tempIdeaText.includes(tags[t].fields.label) === false)) {
                // console.log("KILLING THE TAG " + tags[t].fields.label);
                // decrement the tag if it occured in the old idea and no longer occurs in the new idea
            }
        }
    }   

    var prevComments = sortedIdeas[tempCategory][i].comments;
    var currentComments;

    for (var x = 0; x <= i; x++){
    /*
        Iterate through the list, shifting all elements to the right by one, until the
        position of the modified idea is reached - this should not be shifted as everything 
        after it will not have their order affected
    */  
        // need to hold on to the current idea temporarily as its current position in the array is to be used for the element before it
        currentIdea = sortedIdeas[tempCategory][x].idea;
        currentComments = sortedIdeas[tempCategory][x].comments;
        
        sortedIdeas[tempCategory].splice(x, 1, { 
            idea: prevIdea, 
            comments: prevComments
        });
        
        prevIdea = currentIdea;
        prevComments = currentComments;

    }
}

function initCollabSocket(){
   

}


window.onbeforeunload = function(e){
    ideaSocket.close();
    tagSocket.close();
    commentSocket.close();
    collabSocket.send(JSON.stringify({
            "function": "removeActiveUser",
            "user": loggedInUser,
    }));

    collabSocket.close();
};
