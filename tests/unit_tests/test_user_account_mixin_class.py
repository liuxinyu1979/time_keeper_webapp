from user.useraccount import UserAccount

def test_creation_successful():
    a_user = {'name':'a', 'email':'b', 'password':'c'}
    ua = UserAccount(a_user)
    assert ua.get_email() == a_user['email']
    assert ua.get_id() == a_user['name']
    assert ua.is_authenticated() == True
    assert ua.is_active() == True
    assert ua.is_anonymous() == False

