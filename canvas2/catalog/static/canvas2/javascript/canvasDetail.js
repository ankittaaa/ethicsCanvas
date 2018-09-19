/*
***************************************************
Do the tag bar thing on the canvas PAGE so that it allows user to navigate back and add and remove colabs accordinglyy


*/




/*
****************
    GLOBALS
****************
*/
var canvasPK;
var projectPK;

var ethicsTitles = [
    {id:"Individuals Affected",popup:"Who use your product or service? Who are affected by its use? Are they men/women,of different ages,etc?"},
        {id:"Behaviour",popup:"How might people's behaviour change because of your product or service? Thei habits, time schedules, choice of activities, etc?"},
      {id:"What can we do?",popup:"What are the most important ethical impacts you found? How can you address these by changing your design, organisation, or by proposing broader changes?"},
      {id:"Worldviews",popup:"How might people's worldviews be affected by your product or service? Their ideas about consumption, religion, work, etc?"},
      {id:"Groups Affected",popup:"Which groups are involved in the design, production, distribution and use of your product or service? Which groups might be affected by it? Are these work-related organisation, interest groups, etc?"},
      {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},

];

var businessTitles = [
  {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
];
//not yet defined about the columns it would have
var privacyTitles = [
  {id:"Individuals Affected",popup:"hey"},
      {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},
    {id:"Individuals Affected",popup:"hey"},

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

var theTitles;

// sortedIdeas will become a 2d array of objects. the 'i' indices will be the categories, while the
// 'j' indices will be an object encapulating an idea and an array of its comments ( { idea, comments[] } )
//let it remain this way in a form of 2d array
var sortedIdeas = new Array(10);
var typingBools = new Array(10);
var typingUser = new Array(10);




var users;
var admins;
var nameAdmins = [];
var UsersActive = [];
var loggedInUser
var isAuth;
var isAdmin;
var selection;
var currentURL;

var thisCanvas;
var allTags = [];
var tags = [];
var tagedCanvas = [];
var tagedideas = [];
var ideas;
var comments;

var tagButtons;
var ideaListComponent;

var ideaWebsocket;
var commentWebsocket;
var tagWebsocket;
var collabWebsocket;


var typingEntered = false;
// initialising the variable as a timeout handler
var typingTimer = setInterval(
            function(){ console.log()}
            , 0);

window.clearTimeout(typingTimer);


$j(document).ready(function(data){


    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // It sends token localy that is relative URLs
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

    // The initial AJAX request to render information on the page
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
    users.push(tempUser);
}

function addUserFailureCallback(data){
    console.log(data);
}

function deleteUserSuccessCallback(data){
    var userListIndex = JSON.parse(data.userListIndex);
    var victimIsAdmin = JSON.parse(data.victimIsAdmin);

    if (users[userListIndex].fields.username === UserLoggedIn .fields.username){
        alert("You've been removed from the project");
        // timeout handler to go back to project page after 2 secs
        setInterval(
            function(){
                window.location.href="/catalog/project-list/"
            },
            100);
    }
    users.splice(userListIndex, 1);
    /*
        We dont require admin - permission  -  callbacks in here unlike the previous page
    */
}

function deleteUserFailureCallback(data){
    console.log(data);
}


function newActiveUserCallback(data){

    user = data.user;
    UsersActive.push(user.fields.username);
    data = {
        'function': 'sendWholeList',
        'users': UsersActive,
    }

    collabWebsocket.send(JSON.stringify({
        'data': data
    }));
}

function wholeListCallback(data){

    if (data.users.length <= UsersActive.length)
        return;
    else
    {
        for (u in data.users){
            if (UsersActive.includes(data.users[u]))
                continue;
            else
                UsersActive.push(data.users[u]);
        }
    }
}

function removeActiveUserCallback(data){

    user = data.user;
    i = UsersActive.indexOf(user.fields.username);

    if (i > -1)
        UsersActive.splice(i, 1);
}


function promoteUserSuccessCallback(data){
    var tempAdmin = JSON.parse(data.admin);
    admins.push(tempAdmin);
    nameAdmins.push(tempAdmin.fields.username);

    if (UserLoggedIn .fields.username === tempAdmin.fields.username)
    {
        isAdmin = true;
        ideaListComponent.admin = true;
    }
}

function promoteUserFailureCallback(data){
    console.log(data);
}

function demoteAdminSuccessCallback(data){
    var adminListIndex = JSON.parse(data.adminListIndex);
    var victimName = nameAdmins[adminListIndex];
    admins.splice(adminListIndex, 1);
    nameAdmins.splice(adminListIndex, 1);

    if (UserLoggedIn .fields.username === victimName)
    {
        isAdmin = false;
        ideaListComponent.admin = false;
    }
}

function demoteAdminFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                                IDEA CALLBACKS
*************************************************************************************************************/
function deleteIdeaSuccessCallbackAJAX(data){
    ideaWebsocket.send(JSON.stringify({
        'function': 'deleteIdea',
        'data': data,
    }));
}

function deleteIdeaSuccessCallback(data){

    for (d in data.returnTagData){

        var dataForTagRemoveSuccess = {
            'tagedCanvas': (data.returnTagData[d].tagedCanvas),
            'taggedIdeas': (data.returnTagData[d].taggedIdeas),
            'tag': (data.returnTagData[d].tags)
        };

        removeTag(dataForTagRemoveSuccess);
    }

    var tempIdea = JSON.parse(data.idea);

    // do nothing if it's not the right canvas

    if (tempIdea.fields.canvas == canvasPK){
        // remove the victim {idea, [comments]} from the sorted ideas list
        var ideaListIndex = JSON.parse(data.ideaListIndex);
        var tempCategory = JSON.parse(data.ideaCategory);

        var tempIdea = sortedIdeas[tempCategory][ideaListIndex].idea;

        if (sortedIdeas[tempCategory].length === 1){
            sortedIdeas[tempCategory].splice(ideaListIndex, 1, {
                idea: null,
                comments: []
            });
        }
        else {
            sortedIdeas[tempCategory].splice(ideaListIndex, 1);
        }

        typingBools[tempCategory].splice(ideaListIndex, 1);
        typingUser[tempCategory].splice(ideaListIndex, 1);
    }
}

function deleteIdeaFailureCallback(data){
    console.log(data);
}

function newIdeaSuccessCallbackAJAX(data){
        // ideaWebsocket.send(JSON.stringify({
        //     'function': 'addIdea',
        //     'data': data,
        // }));
}

function newIdeaSuccessCallback(data){
/*
    Function for updating the idea list for the modified category
    upon addition of new or deletion of current idea
*/
    var tempIdea;
    if (isAuth === false){
        tempIdea = JSON.parse(data.idea);
    }
    else
        tempIdea = JSON.parse(data.idea);

    if (tempIdea.fields.canvas != canvasPK)
        return;

    var tempCategory = tempIdea.fields.category;
    var newIdea = {
        idea: tempIdea,
        comments: []
    };

    // since ideas are sorted from newest to oldest, push the new idea to the front of sortedIdeas for the category
    // and an empty array for the comments, as a brand-new idea has no comments yet
    if (sortedIdeas[tempCategory][0].idea === null)
    {
        sortedIdeas[tempCategory].splice(0, 1, newIdea);
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
    console.log(data);
}

function editIdeaSuccessCallbackAJAX(data){
    ideaWebsocket.send(JSON.stringify({
            'function': 'modifyIdea',
            'data': data,
        }));
}

function editIdeaSuccessCallback(data){

    var inIdea = (JSON.parse(data.idea));

    // update the idea iff it's the right idea
    if (inIdea.fields.canvas == canvasPK){
        var tempCategory = inIdea.fields.category;
        var ideaListIndex = JSON.parse(data.ideaListIndex);
        var oldText = escapeHTMLChars(data.oldText);
        sortIdeas(inIdea, ideaListIndex, tempCategory, oldText);
    }

    for (d in data.newReturnTagData){

        var dataForTagAddition = {
            'tagedCanvas': (data.newReturnTagData[d].newtagedCanvas),
            'taggedIdeas': (data.newReturnTagData[d].newTaggedIdeas),
            'tag': (data.newReturnTagData[d].newTag)
        };
        newTagSuccessCallback(dataForTagAddition);
    }

    for (d in data.removedReturnTagData){
        var dataForTagRemoval = {
            'tagedCanvas': (data.removedReturnTagData[d].removedtagedCanvas),
            'taggedIdeas': (data.removedReturnTagData[d].removedTaggedIdeas),
            'tag': (data.removedReturnTagData[d].removedTag)
        };
        removeTag(dataForTagRemoval);
    }
}

function editIdeaFailureCallback(data){
    console.log(data);
}


function typingCallback(data, f){
    var canvas = data.canvasPK;

    if (canvas != canvasPK)
        return;

    var tempCategory = data.ideaCategory;
    var tempName = data.username;
    var ideaListIndex = data.ideaListIndex;

    // do nothing, the logged in user knows when they're typing
    if (tempName == UserLoggedIn .fields.username)
        return;

    if (f === "typing"){
        typingUser[tempCategory].splice(ideaListIndex, 1, tempName);
        typingBools[tempCategory].splice(ideaListIndex, 1, true);
    }
    else {
        typingUser[tempCategory].splice(ideaListIndex, 1, '');
        typingBools[tempCategory].splice(ideaListIndex, 1, false);
    }



}
/*************************************************************************************************************
                                        COMMENT CALLBACKS
*************************************************************************************************************/


function commentSuccessCallbackAJAX(data){
    commentWebsocket.send(JSON.stringify({
        'data': data,
    }))
}

function newCommentSuccessCallback(data){
    var ideaListIndex = JSON.parse(data.ideaListIndex);
    var returnComment = JSON.parse(data.comment);
    var tempCategory = JSON.parse(data.ideaCategory);
    sortedIdeas[tempCategory][ideaListIndex].comments.unshift(returnComment);
}

function addCommentFailureCallback(data){
    console.log(data);
}


function deleteCommentSuccessCallback(data){
    var ideaListIndex = JSON.parse(data.ideaListIndex);
    var commentListIndex = JSON.parse(data.commentListIndex);
    var tempCategory = JSON.parse(data.ideaCategory);

    sortedIdeas[tempCategory][ideaListIndex].comments.splice(commentListIndex, 1);
}

function deleteCommentFailureCallback(data){
    console.log(data);
}

function resolveIndividualCommentSuccessCallback(data){
    var ideaListIndex = JSON.parse(data.ideaListIndex);
    var commentListIndex = JSON.parse(data.commentListIndex);
    var tempCategory = JSON.parse(data.ideaCategory);

    var tempComment = sortedIdeas[tempCategory][ideaListIndex].comments[commentListIndex];

    tempComment.fields.resolved = true;
    sortedIdeas[tempCategory][ideaListIndex].comments.splice(commentListIndex, 1, tempComment);
}

function resolveIndividualCommentFailureCallback(data){
    console.log(data);
}

function resolveAllCommentsSuccessCallback(data){
    var tempCategory = JSON.parse(data.ideaCategory);
    var ideaListIndex = JSON.parse(data.ideaListIndex);

    // empty the comments for the idea
    var length = sortedIdeas[tempCategory][ideaListIndex].comments.length;
    var tempComment;

    for (var c = 0; c < length; c++)
    {
        tempComment = sortedIdeas[tempCategory][ideaListIndex].comments[c];
        tempComment.fields.resolved = true;
        sortedIdeas[tempCategory][ideaListIndex].comments.splice(c, 1, tempComment);
    }
}
function resolveAllCommentsFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                            TAG CALLBACKS
*************************************************************************************************************/

function newTagSuccessCallbackAJAX(data){
    tagWebsocket.send(JSON.stringify({
        'data': data,
    }))
}

function newTagSuccessCallback(data){
    // re-execute these steps so a new tag will, on being clicked, show it's in the current canvas
    var newTag = JSON.parse(data.tag);
    var temptagedCanvas = JSON.parse(data.tagedCanvas);
    var tempTaggedIdeas = JSON.parse(data.taggedIdeas);
    var i = -1;
    var canvasTagged = false;


    for (t in tags){
        if (tags[t].pk == newTag.pk){
            i = t;
            break;
        }
    }

    for (tc in temptagedCanvas){
        if (temptagedCanvas[tc].pk == canvasPK){
            canvasTagged = true;
            break;
        }
    }

    // if the tag doesn't exist (index === -1), but the canvas is tagged by it, add it
    if (canvasTagged === true){
        if (i === -1){
            if (tags[0].pk !== null){
                tags.push(newTag);
                tagedCanvas.push(temptagedCanvas);
                tagedideas.push(tempTaggedIdeas);
            }
            else {
                tags.splice(0, 1, newTag);
                tagedCanvas.splice(0, 1, temptagedCanvas);
                tagedideas.splice(0, 1, tempTaggedIdeas);
            }
        }


        // if the tag DOES exist (index > -1) and the canvas is tagged by it, update it
        else{
            tagedCanvas.splice(i, 1, temptagedCanvas);
            tagedideas.splice(i, 1, tempTaggedIdeas);
        }
    }



    // otherwise do nothing
}

function newTagFailureCallback(data){
    console.log(data);
}


function removeTag(data){
    // differs to deleteTag in that it is called when a tag's occurrences in a canvas are altered.
    // the tag's presence may still be in that canvas and in other canvases, so it shouldn't be deleted.
    // instead the set of ideas is altered.

    var victimTag = JSON.parse(data.tag);
    var temptagedCanvas = JSON.parse(data.tagedCanvas);
    var tempTaggedIdeas = JSON.parse(data.taggedIdeas);

    var tagExists = false;
    var canvasTagged = false;
    var tagIndex = -1;



    for (i in tags){
        if (tags[i].pk == victimTag.pk){
            tagExists = true;
            tagIndex = i;
        }
        for (j in temptagedCanvas){
            if (temptagedCanvas[j].pk == canvasPK){
                canvasTagged = true;
            }
        }
    }

    // if the tag does exist, but the canvas is not tagged by it, remove it
    if (tagExists === true && canvasTagged === false){
        if (tags.length > 0 && tags.length != 1){
            // simply remove the tag if there will be more remaining
            tags.splice(tagIndex, 1);
            tagedCanvas.splice(tagIndex, 1);
            tagedideas.splice(tagIndex, 1);
        }
        else {
            // if removing last tag, replace with null tag
            var tempTag = tags[0];
            tempTag.pk = null;
            tempTag.fields.date_created = null;
            tempTag.fields.date_modified = null;
            tempTag.fields.label = null;
            tags.splice(0, 1, tempTag);
            tagedCanvas.splice(0, 1);
            tagedideas.splice(0, 1);
        }
        return;
    }
    // if the tag does exist and the canvas is tagged by it, update it to reflect removal form other canvases
    else if (tagExists === true && canvasTagged === true){
        tagedCanvas.splice(tagIndex, 1, temptagedCanvas);
        tagedideas.splice(tagIndex, 1, tempTaggedIdeas);

    }

        // otherwise do nothing

}

function deleteTagSuccessCallbackAJAX(data){
    tagWebsocket.send(JSON.stringify({
        'data': data,
    }))
}


function deleteTagSuccessCallback(data){
    var tag = JSON.parse(data.tag);
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
            tagedCanvas.splice(i, 1);
            tagedideas.splice(i, 1);
        }
        else {
            // if last tag, replace with null tag
            var tempTag = tags[i];
            tempTag.pk = null;
            tempTag.fields.date_created = null;
            tempTag.fields.date_modified = null;
            tempTag.fields.label = null;
            tags.splice(i, 1, tempTag);
            tagedCanvas.splice(0, 1);
            tagedideas.splice(0, 1);
        }
    }


}

function deleteTagFailureCallback(data){
    console.log(data);
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

    UserLoggedIn  = JSON.parse(data.UserLoggedIn );
    projectPK = JSON.parse(data.projectPK);
    thisCanvas = JSON.parse(data.thisCanvas);

    canvasType = thisCanvas.fields.canvas_type;
    users = JSON.parse(data.users);
    admins = JSON.parse(data.admins);

    if (UserLoggedIn .length == 0){
        isAuth = false;
    }

    else {
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

        for (a in admins)
        nameAdmins.push(admins[a].fields.username);

        if (nameAdmins.indexOf(UserLoggedIn .fields.username) !== -1)
            isAdmin = true;
        else
            isAdmin = false;

        $j('#canvas-title').html(thisCanvas.fields.title);
        var inTags = JSON.parse(data.tags);

        // if tags exist - the zeroth tag won't be null
        if (inTags.pk === null){
            tags.push(inTags);
            tagedideas = [];
            tagedCanvas = [];
        }

        else {
            var i;
            for (i = 0; i < inTags.length; i++){
                tags.push((inTags[i]));
                tagedideas.push(JSON.parse(data.tagedideas[i]));
                tagedCanvas.push(JSON.parse(data.tagedCanvas[i]));

            }
        }
    }
    else {
        $j('#canvas-title').html("Trial Canvas");

        // only want to initialise the ideaWebsocket so that new idea JSON objects can be acquired - NOT ADDED TO A CANVAS
    }

    if (canvasType === 0)
        theTitles = ethicsTitles;
    else if (canvasType === 1)
        theTitles = businessTitles;
    else if (canvasType === 2)
        theTitles = privacyTitles;


    ideaListComponent = new Vue({
        el: '#idea-div',
        data: {
            ideaList: sortedIdeas,
            categories: theTitles,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
            adminNameList: nameAdmins,
        }
    })

    if (isAuth === true){
        tagButtons = new Vue({
            el: '#tag-div',
            data: {
                tagList: tags,
                canvasList: tagedCanvas,
                ideaList: tagedideas,
                show: false,
                auth: isAuth,
            },
        })
    }
}

function initFailureCallback(data){
    console.log(data);
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
            categories: theTitles,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
            adminNameList: nameAdmins,
        }
    },

    template:`
    <div>
    <table>
    <tr>
    <td rowspan="2" bgcolor="#a67de0" valign="top" >
    </td>
    <td class="one" bgcolor="#85ade5" valign="top">
    </td>
    <td rowspan="2" bgcolor="#8b99e0" valign="top" >
    </td>
    <td class="one"   bgcolor="#15af97" valign="top" >
    </td>
     <td rowspan="2" bgcolor="#a67de0" valign="top" >
     </td>
    </tr>
    <tr>
    <td bgcolor="#aed581" valign="top" >
   </td>
   <td bgcolor="#85ade5" valign="top" >
   </td>
   </tr>
    </table>
    <table>
    <tr>
     <td class="three" bgcolor="#85ade5" valign="top" >
     </td>
        <td class="three" bgcolor="#aed581" valign="top" >
        </td>
        </tr>
    <tr>
      <td class="two" colspan="2" bgcolor="#a67de0" valign="top" >
      </td>
      </tr>
      </table>
    </div>
  `,

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
            max:100
        }
    },

    template:`    <div class="masonry">
                 <div v-bind:class="this.flexClass" >

                    <h3><% title()%>&emsp;&emsp;&emsp;&emsp;
                    <hr><h3><strong><% popup()%></strong></h3>

                    <i class="material-icons">help</i>
                    </h3>


                    <div class="idea-container" v-if="escapedIdeas[0]" >
                    <div v-for="(idea, ideaListIndex) in escapedIdeas">
                    <div v-bind:id=textID(ideaListIndex)>
                    <textarea class="idea-input"
                                    type="text" v-model="idea.fields.text"
                                    :maxlength="max"
                                    @blur="changed($event, idea, ideaListIndex)"
                                    @keydown="keydownCallback($event, idea, ideaListIndex)"
                                    @keypress="setTyping($event, idea, ideaListIndex)"
                                    @paste="setTyping($event, idea, ideaListIndex)"
                                    placeholder="Enter an idea"/>

                                    <p id="user-typing" v-show="isTypingBools[ideaListIndex] == true">
                                        <%typingUser[ideaListIndex]%> is typing...
                                    <p v-text="(max - idea.fields.text.length)"  color="white"><p>characters remaining</p></p>
                            </div>

                            <div class='idea-buttons'>

                            <div v-if="isAuth">
                                <button id="comment-button" class="btn btn-link" v-on:click="displayMe(ideaListIndex)">
                                    <span> <i class="material-icons">chat_bubble</i>(<% commentList[ideaListIndex].length %>)</span>
                                </button>
                                <comment v-show=showCommentThread[ideaListIndex] v-bind:commentList="commentList[ideaListIndex]" v-bind:idea="idea" v-bind:ideaListIndex="ideaListIndex" v-bind:admins="adminNameList" @close="displayMe(ideaListIndex)">
                                </comment>
                            </div>

                            <div v-else>
                                <button id="comment-button"  class="btn btn-link" title="Sign up to use this feature" disabled>
                                <i class="material-icons">chat_bubble</i>
                                </button>
                            </div>
                              <div v-if="isAuth">
                                <button id="move-idea" class="btn btn-link" v-on:click="movingidea()">
                                <i class="material-icons">format_list_bulleted</i>
                                </button>
                                </div>
                                <div v-else>
                                <button id="move-idea" class="btn btn-link" title="Sign up to use this feature" disabled>
                                    <i class="material-icons">format_list_bulleted</i>
                                    </button>
                                </div>
                                <button class="btn btn-link" @click="upIdea($event, idea, ideaListIndex)"><i class="material-icons">keyboard_arrow_up</i></button>
                                <button class="btn btn-link"><i class="material-icons">keyboard_arrow_down</i></button>
                                <button id="delete-idea" class="btn btn-link" @click="deleteIdea($event, idea, ideaListIndex)" title="delete"><i class="material-icons">highlight_off</i><br/></button>

                                   <button v-if="escapedIdeas[0]" id="new-tag-button" class="btn btn-link"  color:white v-on:click="newTag()"><br/><i class="material-icons">local_offer</i>Tag Selected Term</button>
                            </div>
                           </div>

                            </div>
                    <div class="main-idea-buttons">
                         <a href="#"  @click="newIdea($event)" style="color:white"> <i class="material-icons">lightbulb_outline</i>Add an idea</a>
                         </div>

              </div>
              </div>

    `,

    computed: {
        ideaList: {
            get: function(){
                var list = []
                    if (this.ideas[0] !== null){
                        for (i in this.ideas){
                            list.push(this.ideas[i].idea)
                        }
                    }
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

        adminNameList: function(){
            return this.nameAdmins
        },

        flexClass: function(){
          var i = this.index
             return "idea-flex-container-" + i

        },

        ideaCategory: function(){
            return ethicsTitles[this.index]
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

        textID: function(ideaListIndex){
            return "idea-category-"+this.index+"-idea-"+ideaListIndex
        },
        pop: function(event){

     $("a[data-toggle='tooltip']").on("click",function(){
       return false;
     });

            //$('[data-toggle="popover"]').popover();
        },
        movingidea:function(){

        },

        displayMe(ideaListIndex){
        /*
            For setting an individual truth value to display a single modal component's comment thread, or to close it.
            This method is required as Vue doesn't detect array changes normally.
        */
            Vue.set(this.showCommentThread, ideaListIndex, !this.showCommentThread[ideaListIndex])
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
        },

        title: function(){
                 var cat = this.categoryList[this.index]

                 var returnCat = []
                 var returntitle =[]
                 var final = ''
                  var i
               for (c in cat){

                     returntitle =  cat[c].slice( 0,cat[c].length)
                      returnCat +=  cat[c].slice( 0,cat[c].length)

                }
                       for(i=0;i<20;i++)
                       final +=  returnCat[i]
                 return final
             },
        popup: function(){
            var cate = this.categoryList[this.index]

            var returnCate = ''


            for (c in cate){
                var upperCate = cate[c]
                returnCate = upperCate
            }

            return returnCate
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
                var url = '/catalog/new_idea/'
                var data = {
                    'function': 'addIdea',
                    'idea_category': this.index,
                    'canvas_pk': canvasPK
                }
                performAjaxPOST(url, data, function placeholder(){}, newIdeaFailureCallback)
            }
            else {
                var url = '/catalog/new_trial_idea/'
                var data = {
                    'function': 'addIdea',
                    'idea_category': this.index,
                    'canvas_pk': canvasPK
                }
                // trial user gets no socket
                performAjaxPOST(url, data, newIdeaSuccessCallback, newIdeaFailureCallback)
            }
        },

        deleteIdea(event, idea, ideaListIndex){
            if (isAuth === true){
                var url = '/catalog/delete_idea/'
                var data = {
                    'function': 'deleteIdea',
                    'idea_pk': idea.pk,
                    'idea_list_index': ideaListIndex
                }
                performAjaxPOST(url, data, function placeholder(){}, deleteIdeaFailureCallback)

            }
            else
                sortedIdeas[this.index].splice(ideaListIndex, 1)
        },

      upIdea(event, idea, ideaListIndex){
                sortedIdeas[this.index].splice(ideaListIndex, 1)
        },


        changed(event, idea, ideaListIndex){
            var text = escapeChars(event.target.value)
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()

            if (isAuth === true){
                window.clearTimeout(typingTimer)
                var url = '/catalog/edit_idea/'
                var data = {
                    'function': 'modifyIdea',
                    'input_text': text,
                    'idea_pk': idea.pk,
                    'idea_list_index': ideaListIndex,
                }
                performAjaxPOST(url, data, function placeholder(){}, editIdeaFailureCallback)

                // if a user entered loads of whitespace, then replace current input field with trimmed text
                event.target.value = text
                idea.fields.text = text
                event.target.blur()
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, ideaListIndex: ideaListIndex, index: this.index})
                    , 0
                )
            }
            else {
                currIdea = sortedIdeas[this.index][ideaListIndex].idea
                currIdea.fields.text = text

                if (sortedIdeas[this.index].length > 1){
                    sortIdeas(currIdea, ideaListIndex, this.index, "")
                }
                else{
                    sortedIdeas[this.index].splice(ideaListIndex, 1, {
                        idea: currIdea,
                        comments: []
                    })
                }

            }

        },

        keydownCallback(event, idea, ideaListIndex){
            key = event.key

            if (key == "Enter")
                event.target.blur()

            if (key == "Escape")
                this.ideaList[ideaListIndex].fields.text = this.ideaList[ideaListIndex].fields.text
        },

        setTyping(event, idea, ideaListIndex){
            if (isAuth === true){

                window.clearTimeout(typingTimer)

                // only want to send something down the socket the first time this function is called
                if (typingEntered == false){
                    data = {
                        'function': 'typing',
                        'ideaCategory': this.index,
                        'username': UserLoggedIn .fields.username,
                        'ideaListIndex': ideaListIndex,
                        'canvasPK': canvasPK
                    }

                    ideaWebsocket.send(JSON.stringify({
                        'data': data,
                    }))
                }

                typingEntered = true

                // timeout function for clearing the <user> is typing message on other windows - waits 2s
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, ideaListIndex: ideaListIndex, index: this.index})
                    , 2000
                )
            }
        },

        newTag(){
            if (isAuth === true){

                var url = '/catalog/add_tag/'
                var data = {
                    'function': 'addTag',
                    'label': selection,
                    'canvas_pk': canvasPK,
                }
                performAjaxPOST(url, data, function placeholder(){}, newTagFailureCallback)

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
    props: ['comment-list', 'show-comments', 'idea', 'ideaListIndex', 'admins'],
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
                            <li v-for="(comment, commentListIndex) in commentList">
                                <div class="comment-elem" v-if="comment.fields.resolved == false">
                                    <% comment.fields.text %>
                                    </br>
                                    <% commentAuthorString(comment) %>
                                    <div v-show="isAdmin">
                                        <button class="delete-comment" @click="deleteComment($event, comment, commentListIndex)" title="delete">Delete</button>
                                        <button class="resolve-individual-comment"
                                                @click="resolveIndividualComment($event, comment, commentListIndex)"
                                                title="delete">Resolve
                                        </button>
                                    </div>
                                </div>
                                <div class="comment-elem resolved" v-else>
                                    <% comment.fields.text %> <strong> <% " (RESOLVED)" %> </strong>
                                    </br>
                                    <% commentAuthorString(comment) %>
                                    <button v-show="isAdmin" class="delete-comment" @click="deleteComment($event, comment, commentListIndex)" title="delete">Delete</button>
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
            return this.ideaListIndex
        },
        nameAdmins: function(){
            return this.admins
        },
        isAdmin: function(){
            return (this.nameAdmins.includes(UserLoggedIn .fields.username))
        },
    },

    watch: {
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

            var url = '/catalog/new_comment/'
            var data = {
                'function': 'addComment',
                'input_text': text,
                'idea_list_index': this.selfIndex,
                'idea_pk': this.currentIdea.pk
            }
            // commentSuccessCallbackAJAX to send data to commentWebsocket for propagation
            performAjaxPOST(url, data, function placeholder(){}, addCommentFailureCallback)
        },

        deleteComment(event, comment, commentListIndex){
            var url = '/catalog/delete_comment/'
            var data = {
                'function': 'deleteComment',
                'comment_pk': comment.pk,
                'idea_list_index': this.selfIndex,
                'comment_list_index': commentListIndex
            }
            // commentSuccessCallbackAJAX to send data to commentWebsocket for propagation
            performAjaxPOST(url, data, function placeholder(){}, deleteCommentFailureCallback)
        },

        resolveIndividualComment(event, comment, commentListIndex){
            var url = '/catalog/resolve_individual_comment/'
            var data = {
                'function': 'resolveIndividualComment',
                'comment_pk': comment.pk,
                'idea_list_index': this.selfIndex,
                'comment_list_index': commentListIndex
            }
            // commentSuccessCallbackAJAX to send data to commentWebsocket for propagation
            performAjaxPOST(url, data, function placeholder(){}, resolveIndividualCommentFailureCallback)
        },

        resolveAllComments(idea){
            var url = '/catalog/resolve_all_comments/'
            var data = {
                'function': 'resolveAllComments',
                'idea_list_index': this.selfIndex,
                'idea_pk': this.currentIdea.pk
            }
            // commentSuccessCallbackAJAX to send data to commentWebsocket for propagation
            performAjaxPOST(url, data, function placeholder(){}, resolveAllCommentsFailureCallback)
        },

        getCommentAuthor(comment){
            var userPK = comment.fields.user

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
    }
})
/*************************************************************************************************************
                                            POPUP COMPONENT
*************************************************************************************************************/
/*Vue.component('popup',{
    props:['title'],
    delimiters:['<%', '%>'],
    template: '#popup',
    data:function(){
      return{
      popups: [
          {
            id: 1,
            title: 'individuals affected',
          },
          {
            id: 2,
            title: 'behaviour',
          },
          {
            id: 3,
            title: 'what can we do'
          }
        ],
        showPopup: false,
    timer: '',
    isInInfo: false
  }},

    methods:{

        hover: function()
        {
          let vm = this;
          this.timer = setTimeout(function() {
            vm.showPopover();
          }, 600);
        },

        hoverOut: function()
        {
          let vm = this;
          clearTimeout(vm.timer);
          this.timer = setTimeout(function() {
            if(!vm.isInInfo)
            {
              vm.closePopover();
            }
          }, 200);
        },

        hoverInfo: function()
        {
          this.isInInfo = true;
        },

        hoverOutInfo: function()
        {
          this.isInInfo = false;
          this.hoverOut();
        },

        showPopover: function()
        {
          this.showPopup = true;
        },

        closePopover: function()
        {
          this.showPopup = false;
        }
    	}
    })*/

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
            canvasList: tagedCanvas,
            tagList: tags,
            auth: isAuth,
            ideaList: tagedideas,
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
        }
    },

    methods: {
        tagInfo: function(event, index){
        },
        exitTagInfo: function(event){
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
            canvas: '',
            selfTag: this.tag,
        }
    },

    template:
        `
            <modal>
                <div slot="header">
                 <i class="material-icons">chat_bubble</i>
                <h3><% label %></h3></i>
                <h4>Appears in: </h4>
                </div>
                <ul slot="body">
                    <li v-for="canvas in this.canvases" style="list-style-type:none;">
                        <a v-bind:href="url(canvas)" target="_blank">
                            <% tagLink(canvas) %>
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
    },

    watch: {
        ideas: function(){

        },
        canvases: function(){
        }
    },

    methods:{
        url: function(canvas){

            return "/catalog/canvas/" + canvas.pk
        },

        tagLink: function(canvas){
            var ideaString = 'Ideas: '

            for (i in this.ideas){
                if (this.ideas[i].fields.canvas === canvas.pk){
                    ideaString += this.ideas[i].pk + ', '
                }
            }
            ideaString = ideaString.slice(0, ideaString.length - 2)

            return canvas.fields.title + " " + ideaString

        },
        deleteTag: function(event){
            var url = '/catalog/delete_tag/'
            var data = {
                'function': 'deleteTag',
                'label': this.tag.fields.label,
                'canvas_pk': canvasPK,
            }
            performAjaxPOST(url, data, function placeholder(){}, deleteTagFailureCallback)

        }
    },

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

    ideaWebsocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/canvas/' + canvasPK + '/idea/'
    );

    commentWebsocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/canvas/' + canvasPK + '/comment/'
    );


    tagWebsocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/project/' + projectPK + '/tag/'
    );


    collabWebsocket = new WebSocket(
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
    ideaWebsocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data.data.function;

        if (f.includes("typing")) {
            typingCallback(data.data, f);
            return;
        }
        switch(f) {
            case "modifyIdea": {
                if (data.data.error)
                    editIdeaFailureCallback(data.data);
                else
                    editIdeaSuccessCallback(data.data);
                break;
            }
            case "addIdea": {
                if (data.data.error)
                    newIdeaFailureCallback(data.data);
                else

                    newIdeaSuccessCallback(data.data);
                break;
            }
            case "deleteIdea": {
                if (data.data.error)
                    deleteIdeaFailureCallback(data.data);
                else
                    deleteIdeaSuccessCallback(data.data);
                break;
            }
        }
    };

    /***********************************
                COMMENT SOCKET
    ************************************/
    commentWebsocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data.data.function;

        switch(f) {
            case "addComment": {
                if (data.data.error)
                    CommentFailureCallback(data.data);
                else
                    newCommentSuccessCallback(data.data);
                break;
            }
            case "deleteComment": {
                if (data.data.error)
                    deleteCommentFailureCallback(data.data);
                else
                    deleteCommentSuccessCallback(data.data);
                break;
            }
            case "resolveIndividualComment": {
                if (data.data.error)
                    resolveIndividualCommentFailureCallback(data.data);
                else
                    resolveIndividualCommentSuccessCallback(data.data);
                break;
            }
            case "resolveAllComments": {
                if (data.data.error)
                    resolveAllCommentFailureCallback(data.data);
                else
                    resolveAllCommentsSuccessCallback(data.data);
                break;
            }
        }
    };

    /***********************************
                TAG SOCKET
    ************************************/
    tagWebsocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data.data.function;

        switch(f) {
            case "addTag": {
                if (data.data.error)
                    newTagFailureCallback(data.data);
                else
                    newTagSuccessCallback(data.data);
                break;
            }
            case "deleteTag": {
                if (data.data.error)
                    deleteTagFailureCallback(data.data);
                else
                    deleteTagSuccessCallback(data.data);
                break;
            }
        }
    };


    /***********************************
                COLLAB SOCKET
    ************************************/
    collabWebsocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data.data.function;

        switch(f) {
            case "promoteUser": {
                if (data.data.error)
                    promoteUserFailureCallback(data.data);
                else
                    promoteUserSuccessCallback(data.data);
                break;
            }
            case "demoteUser": {
                if (data.data.error)
                    demoteUserFailureCallback(data.data);
                else
                    demoteAdminSuccessCallback(data.data);
                break;
            }
            case "addUser": {
                if (data.data.error)
                    addUserFailureCallback(data.data);
                else
                    addUserSuccessCallback(data.data);
                break;
            }
            case "deleteUser": {
                if (data.data.error)
                    deleteUserFailureCallback(data.data);
                else
                    deleteUserSuccessCallback(data.data);
                break;
            }
            case "newActiveUser": {
                newActiveUserCallback(data.data);
                break;
            }

            case "removeActiveUser": {
                removeActiveUserCallback(data.data);
                break;
            }

            case "sendWholeList": {
                wholeListCallback(data.data);
                break;
            }
        }
    };


    collabWebsocket.onopen = function(e){
        var data = {
            "function": "newActiveUser",
            "user": UserLoggedIn ,
        }
        collabWebsocket.send(JSON.stringify({
            "data": data
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

    data = {
        'function': 'done_typing',
        'ideaCategory': this.index,
        'username': UserLoggedIn .fields.username,
        'ideaListIndex': this.ideaListIndex,
        'canvasPK': canvasPK
    }

    ideaWebsocket.send(JSON.stringify({
        'data': data
    }))
    window.clearTimeout(typingTimer)
    typingEntered = false;
}


function sortIdeas(inIdea, ideaListIndex, tempCategory, oldText){
    /*
        Function called when an idea has been modified, to move the idea and its attached comments to the top of the list,
        where it would be if the page was refreshed. Also checks if any tag occurrences have been removed by checking if the substring
        equal to any tag label existed in the previous idea text field and now no longer occurs
    */
    var prevIdea = inIdea;
    var currentIdea = sortedIdeas[tempCategory][ideaListIndex].idea;

    if (isAuth === true){
        if (tags[0].pk != null){
            for (t in tags){
                // iterate through tags, check for occurrences in old text that no longer exist in new text
                var tempIdeaText = currentIdea.fields.text;

                if ((oldText.includes(tags[t].fields.label) === true) && (tempIdeaText.includes(tags[t].fields.label) === false)) {
                    // decrement the tag if it occured in the old idea and no longer occurs in the new idea
                }
            }
        }
    }

    var prevComments = sortedIdeas[tempCategory][ideaListIndex].comments;
    var currentComments;

    for (var x = 0; x <= ideaListIndex; x++){
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

window.onbeforeunload = function(e){

    if (isAuth){
        ideaWebsocket.close();
        tagWebsocket.close();
        commentWebsocket.close();
        var data = {
            "function": "removeActiveUser",
            "user": UserLoggedIn ,
        }
        collabWebsocket.send(JSON.stringify({
            "data": data
        }));
        collabWebsocket.close();
    }
};
