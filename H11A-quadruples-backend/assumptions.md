# Iteration 2 Assumptions

### H11A-quadruples

Assumptions made when implementing routes for the Slackr app as well as when writing System Tests.

## __General Assumptions__

* The database is not wiped if the server stops running. ie. if I register while the server is running, then stop the server and run it again, then I am still registered.

## __`auth`__

* After a user registers, they are automatically logged in. To be 'logged in', a user needs a valid token, and a valid token is returned by the `auth/register` route.
* Assumed that a user cannot be "unregistered" or deleted. This is a necessary assumption for generating globally unique `u_id`'s.
* Assumed that if a generated handle is greater than 20 characters, then cutoff to be 20 characters long, and that new handle is not unique, then a number can be appended to the handle to make it unique (even though it will now exceed 20 characters long)

## __`channel`__

* Assumed that if a Slackr owner (`permission_id` 1) is invited to, or joins a channel, they are automatically promoted to an `owner_member` (alongside having owner privileges). Our interpretation here was that having "owner privileges" is equivalent to _being_ an owner.
* Assumed that a channel can have 0 members in it.
* Assumed that `channel/messages` returns messages from most recent to least recent, ie. the message in index 0 is the most recent message sent to the channel.
* Assumed that an error is not thrown when start = 0. Normally, an error should be thrown if "start is greater than or equal to the number of messages". If there are no messages and start = 0, then an error would be thrown which is not sensible.
* Assumed that if an owner of a channel leaves that channel, then if they are not a Slackr owner and attempt to join back, they will not re-gain their owner privileges. Slackr owners, however, will gain owner privileges upon leaving and joining back.
* Assumed that all channel owners can modify other owners' channel ownership status. ie, a non Slackr owner (who is also a channel owner) can demote a Slackr owner to a member of the channel. However, if the Slackr owner then leaves and re-joins, they will regain their ownership.
* Assumed that `channel/details` is automatically updated if a user changes their `name_first` or `name_last`, rather than updating after the user leaves and re-joins, for example.

## __`channels`__

* Assumed a channel could not be deleted. This is a necessary assumption for the creation of globally unique `channel_id`'s.
* Assumed that the person who creates a channel is automatically an owner of that channel.

## __`message`__

* Assumed all timestamps are UTC timestamps, not local timestamps.
* Assumed that the edited message can be of any length. The spec does not specify to raise an error if the `message` parameter in `message/edit` is over, say, 1000 characters.
* Assumed that if someone leaves a channel, their reacts stay in the channel (ie. the react count stays the same).

## __`other`__

* Assumed that a Slackr owner can demote themselves to a member. A consequence of this is that it is possible to have 0 Slackr owners in a workspace.
* Assumed that a search query is not case sensitive. ie. the search for `hello` would be the same as the search for `HELLO`. This assumption was made for functionality purposes (easier to search for and find messages).
* Assumed that `workspace/reset` also resets the global uniqueness of all id's. For example, if a `u_id` of 1 exists, and `workspace/reset` is called, then a `u_id` of 1 is now allowed to exist again.

## __`user`__

* Assumed that setting a name does not change a user's handle to a lowercase concatenation of their _new_ `name_first` and `name_last`.

# Iteration 1 Assumptions

### H11A-quadruples

A list of assumptions made when writing Integration Tests for the project.

## __General Assumptions__

* It was assumed that registering a user in a helper function (as seen in `registers.py`) will create a *global* class for that user. This is so that the existence of the user persists beyond the helper function call so that the user can be used for testing.
* Similarly creating a channel by calling a helper function (in `registers.py`) within a test function will create the channel so that the existence of the channel persists beyond the helper function.
* For example, if `chan1()` is a helper function that calls `channels_create()` within its implementation, then:

```
def test_channel():
    id, token = user1()
    channel_id = chan1()

    ## At this point, the channel still exists in the database
    ## Hence calling a function like channels_listall() will not return an empty list
    
    assert channels_listall(token) == {
        'channels': [
        	{
        		'channel_id': 1,        ## this depends on chan1()
        		'name': 'My Channel'
        	}
        ]
    }
```

## __`auth.py`__

##### `auth_login()`

* To test `auth_login()` it was assumed that `auth_register()` was functional.
* Assumed that passwords are case sensitive. This is a very reasonable assumption.

##### `auth_logout()`

* To test `auth_logout()` it was assumed that `auth_register()` was functional.
* Assumed that '11111' is not a valid token. This is a reasonable assumption because authentication tokens typically take the form of a long string of letters, numbers and symbols. It is likely that '11111' will not be the result of a token generation.

##### `auth_register()`

* Assumed that `name_first` and `name_last` must be between 1 and 50 characters *inclusive* and not exclusive, otherwise an InputError is thrown. The assumption made here was the inclusivity of the specification 'between 1 and 50 characters'.
* If two users register with the same `name_first` and `name_last`, it was assumed that the method of generating unique handles for each user would be to suffix the handles with numbers. For example, if a user registers with the handle 'haydensmith', and then a user attempts to register with the name 'Hayden Smith', then their default handle would be 'haydensmith1'. If this was taken, their handle would be 'haydensmith2', and so on...
* It was assumed that `user_profile()` works in order to extract and check a user's `handle_str`.
* Assumed that '11111' and ' ' are both invalid tokens. This is for the same reason as above, however here it is guaranteed that they are indeed invalid due to no users being registered within the `test_auth_access_error()` function at the time.
* Assumed that a name 'Hayden Smith' will result in the handle 'haydensmith' *not* 'hsmith'. This assumption was made because the specification says 'A handle is generated that is the concatentation of a lowercase-only first name and last name.' Note the use of the words 'first *name*' rather than 'first *initial*'.

## `channel.py`

##### `channel_invite()`

* To test `channel_invite()` it was assumed that `auth_register()`, `channels_create()`, `channels_list()`, `users_all()`, `channel_join()` and `channel_details()` all work.

##### `channel_details()`

* To test `channel_details()` it was assumed that `auth_register()`, `channels_create()` and `channels_list()` all work.

##### `channel_messages()`

* To test `channel_messages()` it was assumed that `auth_register()`, `channels_create()`, `message_send()` and `channels_list()` all work.

##### `channel_leave()`

* To test `channel_leave()` it was assumed that `auth_register()`, `channels_create()`, `channels_list()` and `channel_details()` all work.
* It was also assumed that an empty channel can exist when everyone leaves the channel.
* Assumed that if the only owner of a channel leaves, then owner privileges should fall on the second member who joined the channel.

##### `channel_join()`

* To test `channel_join()` it was assumed that `auth_register()`, `channels_create()`, `channels_list()` and `channels_listall()` all work.

##### `channel_addowner()`

* To test `channel_addowner()` it was assumed that `auth_register()`, `channels_create()`, `channel_join()`, `channel_details()` and `channels_list()` all work.
* Assumed that if user A, B and C are all in a channel B that userB has made, and userA is the owner of the Slackr, then userA can call `channel_addowner()` on themselves to make themselves an owner. UserA can then call `channel_removeowner()` on the creator of the channel, userB.

##### `channel_removeowner()`

* To test `channel_removeowner()` it was assumed that `auth_register()`, `channels_create()`, `channel_addowner()`, `channel_details()`, `channel_invite()`, `channels_list()` and `channel_join()` all work.
* Assumed that owners can modify other owners permissions. This includes removing another owner's ownership.

## `channels.py`

##### `channels_list()`

* To test `channels_list()` it was assumed that `auth_register()` and `channels_create()` were functional.
* The order of channels were assumed to be returned in the same order that they were created. For example, if user1 creates channel1 and then channel2, then `channels_list(user1_token)` returns two channels in the order [{channel1}, {channel2}] instead of the other way around.
* It was assumed that `channel_join()` and `channel_leave()` work so that the test coverage of `channels_list()` could be expanded.

##### `channels_listall()`

* To test `channels_listall()` it was assumed that `auth_register()` and `channels_create()` were functional.
* Similarly, the order of the channels were also assumed to be returned in the order they were created.
* Assumed that the function should return the same dictionary regardless of which authorised user makes the request (ie. order should not change).

##### `channels_create()`

* To test `channels_create()` it was assumed that `auth_register()` was functional.
* It was assumed that `channels_list()` worked so that the creation of a channel could be verified.
* In `test_channels_access_error()` it was assumed that by concatenating 50 'a's onto the end of a valid token, an invalid token would be generated. This is fair because within the function, only a single user has been registered.

## `message.py`

##### `message_send()`

* To test `message_send()` it was assumed that `auth_register()` and `channels_create()` were functional.
* It was assumed that `channel_messages()` worked so that the message id returned by `message_send()` could be confirmed to be correct.

##### `message_remove()`

* To test `message_remove()` it was assumed that `auth_register()` and `channels_create()` were functional.
* It was assumed that `message_send()` and `channel_messages()` worked so that a message could be sent and removed and a channel's messages could be checked before and after removing them.
* Assumed that a single call of `channel_messages()` returns a value of end = -1 since there were less than 50 messages in the channel at the time.
* It was assumed that `channel_join()` worked so that a user could join a channel and attempt to remove another user's message without admin privileges, which would invoke an AccessError.

##### `message_edit()`

* To test `message_edit()` it was assumed that `auth_register()` and `channels_create()` were functional.
* It was assumed that `message_send()`, `channel_messages()` and `channel_join()` worked for the same reasons as `message_remove()`.
* In `test_message_access_error()` the same assumption was made for concatenating 50 'a's onto the end of a valid token.

## `other.py`

##### `users_all()`

* To test `users_all()` it was assumed that `auth_register()` and `channels_create()` were functional.
* It was assumed that the list of all users would be in the same order of registration. A direct consequence of this assumption would be that this function should return the same list of users regardless of who makes the request.
* It was assumed that `user_profile_setname()`, `user_profile_setemail()` and `user_profile_sethandle()` all worked to improve test coverage. The user list should be updated whenever one of these functions were called, and this was tested.

##### `search()`

* Assumed that the list of messages returned by this function would be any message that contain `query_str` as a *subset* of the message. Note the use of the word *subset* instead of *proper subset*. This means if the query string is identical to the message, it would still be returned by `search()`.
* Assumed that `query_str` is not case sensitive. This means the search for a string 'hello' should return the same dictionary as the search for a string 'HELLO'. This was assumed to increase the functionality of the function and to mirror the CTRL + F feature of a search engine - which isn't case sensitive. This assumption was tested in `test_search_case_sensitive()`.
* It was assumed that `message_send()`, `auth_register()` and `channels_create()` all work. This assumption is necessary to test the `search()` function.
* It was assumed that the order of messages returned by this function matches the order that the messages were sent. For example, if I send two messages in this order: 'Hello', 'Help', and search for the string 'Hel' then the list of messages that `search()` returns will be ordered so that the message with index 0 will be 'Hello' and the message with index 1 will be 'Help'. In other words, the lower the index, the older the message.
* It was assumed that `channel_join()`, `channel_leave()`, `message_remove()` and `message_edit()` all work to increase test coverage.
* Assumed that an empty list of messages would be returned if `query_str` has no matches.
* A similar assumption was made regarding the invalidity of a token upon suffixing a valid token with a string of 50 'a's.

## `user.py`

##### `user_profile()`

* To test `user_profile()` it was assumed that `auth_register()` was functional.
* Assumed that `user1_id + 99` is an unregistered and invalid id, which is a fair assumption since no other users other than user1 were registered within this test function.

##### `user_profile_setname()`

* To test `user_profile_setname()` it was assumed that `auth_register()` was functional.
* Assumed that `user_profile()` works so that the changes made by `user_profile_setname()` could be confirmed to have succeeded.
* Assumed two users can have the exact same `name_first` and `name_last`.
* Assumed that the specification of `name_first` and `name_last` being 'between 1 and 50 characters' is *inclusive*.
* Assumed that changing a user's name does *not* change the user's handle. Assumed that the handle can only be changed by calling `user_profile_sethandle()`, otherwise the default handle given upon registering stays the same.

##### `user_profile_setemail()`

* To test `user_profile_setemail()` it was assumed that `auth_register()` was functional.
* Assumed that `user_profile()` works so that the changes made by `user_profile_setemail()` could be confirmed to have succeeded.
* Assumed that emails ARE case sensitive (although the domain name is case insensitive). ie. `jameskroeger@gmail.com` and `JAMESKROEGER@gmail.com` are *different emails*.

##### `user_profile_sethandle()`

* To test `user_profile_sethandle()` it was assumed that `auth_register()` was functional.
* Assumed that `user_profile()` works so that the changes made by `user_profile_sethandle()` could be confirmed to have succeeded.
* Assumed that the specification of `handle_str` being 'between 3 and 20 characters' is *inclusive*.
* Assumed that handles ARE case sensitive. ie. `bobross` and `BOBROSS` are different handles.
* A similar assumption was made with regards to generating an invalid token by adding 50 'a's onto the end of a valid token.
