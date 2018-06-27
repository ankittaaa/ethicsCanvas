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
var tagOccurrences = new Array();
var taggedCanvasses;
var allTaggedCanvasses = [];
var ideas;
var comments;

var users;
var admins;
var adminNames = [];
var activeUsers = [];
var loggedInUser
var isAuth;
var isAdmin;
var allCanvasses
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
/*************************************************************************************************************
                                                IDEA CALLBACKS
*************************************************************************************************************/


function deleteIdeaSuccessCallback(data){
    var i = JSON.parse(data.i);
    var tempCategory = JSON.parse(data.category);

    // grab a copy of the victim idea 
    var tempIdeaText = sortedIdeas[tempCategory][i].idea.fields.text;
    
    // search for tags that occur in the victim idea
    for (t in tags){
        if (tempIdeaText.includes(tags[t].fields.label))
            // decrement the tag if it occurs in the victim idea
            tagOccurrences[t]--;
        if (tagOccurrences[t] === 0){
            // delete the tag if it now does not occur 
            var thisTag = tags[t];

            tagSocket.send(JSON.stringify({
                'function': 'removeTag',
                'i': t,
                "tag_pk": thisTag.pk,
                "canvas_pk": canvasPK,
            }));
        }
    }

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

    for (tag in allTags){
        // if the new idea string contains a tag declared in a different canvas
        var tempTag = allTags[tag];
        
        if (inIdea.fields.text.includes(tempTag.fields.label)){
            // add that tag to the current canvas's list
            tagSocket.send(JSON.stringify({
                    'function': 'addTag',
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
    var newTag = JSON.parse(data.tag);
    console.log(newTag);

    // the canvasses must be made aware that a new tag exists in the project, even if they're not using it at the moment
    // this does not append to the vue component's list, but makes it so that when an idea is edited and now contains the 
    // tag's label, it can be found without requiring a page reload first
    allTags.push(newTag[0]);
    
    // if it's a null tag being returned, we should do nothing
    if (newTag[0].fields.label == null)
        return;
    var tagExists = false;
    var isTagged = false;
    var newTagged = JSON.parse(data.taggedCanvasses);
    

    for (t in newTagged){
        if (newTagged[t].pk == canvasPK){
            isTagged = true;
        }
    }

    for (t in tags){
        if (newTag[0].pk === tags[t].pk){
            // do NOT update if the tag is already present!
            tagExists = true;
        }
    }

    // add the tag iff it occurs in this canvas and isn't currently included!
    if (tagExists === false && isTagged === true){

        taggedCanvasses.unshift(new Array(newTagged.length));

        // empty string to signify a "dummy" tag for canvasses which do not contain any actual tags
        if (tags[0].fields.label === "\0")
            // delete the dummy and replace it with the new tag
            tags.splice(0, 1, newTag[0]);
        else
            tags.unshift(newTag[0]);   
        
        
        tagOccurrences.unshift(0);
        thisCanvas.fields.tags = tags;
    }

    for (i in sortedIdeas){
        for (j in sortedIdeas[i]){
            // it's possible that more than one idea in the same canvas contain occurrences of the new tag label
            if (sortedIdeas[i][j].idea === null)
                continue;
            else if (sortedIdeas[i][j].idea.fields.text.includes(newTag[0].fields.label)){
                tagOccurrences[0]++;
            }
        }
    }
    // entry for tagList to show each canvas tagged in - this step is always executed
    // as it's either an update to current tag-holding canvas, or the canvas in which the tag is new
    for (i in newTagged){
        taggedCanvasses[0].splice(i, 1, newTagged[i]);
    }

}

function newTagFailureCallback(data){
    console.log(data.responseText);
}

function removeTagSuccessCallback(data){
    var i = JSON.parse(data.i);
    var newTag = JSON.parse(data.tag)[0];
    var newTagged = JSON.parse(data.taggedCanvasses);

    // if tag exists in this canvas
    if (tagOccurrences[i] != 0){
        // replace old tag with new tag 
        taggedCanvasses.splice(i, 1, newTagged);
    }
    else {
        // otherwise, delete it and its corresponding occurrences count
        tags.splice(i, 1);
        tagOccurrences.splice(i, 1);
    }


}

function deleteTagSuccessCallback(data){
    var i = JSON.parse(data.i);
    var tag = JSON.parse(data.tag)[0];
    
    for (t in tags){
        if (tags[t].fields.label === tag.fields.label){
            tagOccurrences.splice(i, 1);    
            tags.splice(i, 1);
            thisCanvas.fields.tags = tags;
            break;
        }
    }


    // populateTagList();
}

function deleteTagFailureCallback(data){
    // console.log(data.responseText);
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
    tags = JSON.parse(data.tags);
    allTags = JSON.parse(data.allTags);
    // taggedCanvasses = JSON.parse(data.taggedCanvasses);

    for (t in data.allTaggedCanvasses){
        allTaggedCanvasses.push(JSON.parse(data.allTaggedCanvasses[t]))
    }



    loggedInUser = JSON.parse(data.loggedInUser);
    canvasType = JSON.parse(data.canvasType);
    projectPK = JSON.parse(data.projectPK);
    thisCanvas = JSON.parse(data.thisCanvas)[0];
    allCanvasses = JSON.parse(data.allCanvasses);
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
        taggedCanvasses = new Array(tags.length);
        
        for (t in tags){
            tagOccurrences.push(0);
        }

        populateTagList();
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
            if (loggedInUser.length > 0){
                for (t in tags){
                    // keep track of how many times a tag occurs. on deletion of all ideas containing the tag, the occurrences reaches
                    // 0 and the tag is removed 
                    if (ideas[idea].fields.text.includes(tags[t].fields.label))
                        tagOccurrences[t]++;
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




    if (isAuth === true)
        $j('#canvas-title').html(thisCanvas.fields.title);
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
            admin: isAdmin,
        }
    })

    if (isAuth === true){
        tagButtons = new Vue({
            el: '#tag-div',
            data: {
                tagList: tags,
                canvasList: taggedCanvasses,
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
            admin: isAdmin,
        }
    },

    template:'#ideas',
    
    computed: {
    },

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
    props: ['user', 'is-typing', 'ideas', 'index', 'categories', 'is-auth', 'is-admin'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            showComments: false,
            // Array of booleans for displaying individual modal components. As a single boolean, all modals will be rendered instead of the one for the comment thread of the clicked idea. 
            showCommentThread: new Array(this.ideas.length),
            isTypingBools: this.isTyping,
            typingUser: this.user,
            categoryList: this.categories
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
                                <comment v-show=showCommentThread[i] v-bind:commentList="commentList[i]" v-bind:idea="idea" v-bind:i="i" v-bind:isAdmin="isAdmin" @close="displayMe(i)"> 
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
    props: ['comment-list', 'show-comments', 'idea', 'i', 'is-admin'],
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
        }
    },
    
    watch: {
        // commentList: function(){
        //     // console.log(this.commentList)
        // }

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
        // for (c in this.comments) {

        //     // console.log(this.comments[c].fields)
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
            canvasList: taggedCanvasses,
            tagList: [],
            auth: isAuth,
        }
    },


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
    props:['label', 'canvases', 'index'],
    delimiters: ['<%', '%>'],
    data: function(){
        return {
            c: ''
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
                    <li v-for="c in this.canvasData" style="list-style-type:none;">
                        <a v-bind:href="url(c)" target="_blank">
                            <% c.fields.title %>
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
        canvasData: function(){
            return this.canvases
        }
    },

    methods:{
        url: function(c){
            return "/catalog/canvas/" + c.pk
        },
        deleteTag: function(event){
            tagSocket.send(JSON.stringify({
                'function': 'deleteTag',
                'i': this.index,
                'canvas_pk': canvasPK,
                'tag_pk': tags[this.index].pk,
            }));
        }
    },
    created: function(){
        // // console.log(this.canvases)
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
function populateTagList(){
/*
    This function's purpose is to populate a 2D array of canvases. Each 'i' element represents a tag,
    while the 'j' element represents the list of canvases attached to that tag. 
*/
    var tagged = [];

    for (var i = 0; i < tags.length; i++){

        // get a list of all public canvases containing the current tag
        for (var j = 0; j < allCanvasses.length; j++){
            if (allCanvasses[j].fields.tags.includes(tags[i].pk)){
                tagged.push(allCanvasses[j]);
            }
        }

        taggedCanvasses.splice(i, 1, tagged);
        tagged = [];
    }

}


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

        switch(f) {
            case "addTag": {
                newTagSuccessCallback(data);
                break;
            }
            case "removeTag": {
                removeTagSuccessCallback(data);
                break;
            }
            case "deleteTag": {
                deleteTagSuccessCallback(data);
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
            // case "promoteUser": {
            //     promoteUserSuccessCallback(data);
            //     break;
            // }
            // case "demoteUser": {
            //     demoteAdminSuccessCallback(data);
            //     break;
            // }
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
                    tagOccurrences[t]--;
                
                if (tagOccurrences[t] === 0){
                    // remove the tag if it now does not occur 
                    var thisTag = tags[t];

                    tagSocket.send(JSON.stringify({
                        'function': 'removeTag',
                        'i': t,
                        "tag_pk": thisTag.pk,
                        "canvas_pk": canvasPK,
                    }));
                }
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
