//
//  SigUpView.swift
//  Bakkle
//
//  Created by Xiao, Xinyu on 11/20/15.
//  Copyright (c) 2015 Bakkle. All rights reserved.
//

//
//  SignInView.swift
//  Bakkle
//
//  Created by Xiao, Xinyu on 11/13/15.
//  Copyright (c) 2015 Bakkle. All rights reserved.
//

import UIKit

import FBSDKLoginKit

class SignUpView: UIViewController, UITextFieldDelegate {
    
    @IBOutlet weak var closeBtn: UIButton!
    @IBOutlet weak var nameField: UITextField!
    @IBOutlet weak var emailField: UITextField!
    @IBOutlet weak var passwordField: UITextField!
    @IBOutlet weak var confirmPasswordField: UITextField!
    @IBOutlet weak var signUpBtn: UIButton!
    @IBOutlet weak var profileImg: UIImageView!
    @IBOutlet weak var editBtn: UIImageView!
    
    var kbHeight: CGFloat!
    var parentLoginInVC: LoginView? = nil
    var profileVC: ProfileView? = nil
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupButtons()
        
        //text field delegates
        nameField.delegate = self
        emailField.delegate = self
        passwordField.delegate = self
        confirmPasswordField.delegate = self
        
        var tap: UITapGestureRecognizer = UITapGestureRecognizer(target: self, action: "dismissKeyboard")
        self.view.addGestureRecognizer(tap)
    }
    
    override func viewDidAppear(animated: Bool) {
        super.viewDidAppear(animated)
        
        setupProfileImg()
    }
    
    func dismissKeyboard() {
        self.nameField.resignFirstResponder() || self.emailField.resignFirstResponder() || self.passwordField.resignFirstResponder() || self.confirmPasswordField.resignFirstResponder()
    }
    
    func textFieldDidBeginEditing(textField: UITextField) {
        animateViewMoving(true, moveValue: 150)
    }
    
    func textFieldDidEndEditing(textField: UITextField) {
        animateViewMoving(false, moveValue: 150)
    }
    
    func animateViewMoving(up: Bool, moveValue: CGFloat) {
        let movementDuration = 0.5
        let movement = up ? -moveValue : moveValue
        UIView.beginAnimations("animateView", context: nil)
        UIView.setAnimationBeginsFromCurrentState(true)
        UIView.setAnimationDuration(movementDuration)
        self.view.frame = CGRectOffset(self.view.frame, 0, movement)
        UIView.commitAnimations()
    }
    
    func setupButtons(){
        closeBtn.setImage(IconImage().close(), forState: .Normal)
        closeBtn.setTitle("", forState: .Normal)
        editBtn.image = IconImage().edit(UIColor.blackColor())
    }
    
    func setupProfileImg() {
        self.profileImg.image = UIImage(named: "default_profile")
        self.profileImg.layer.cornerRadius = self.profileImg.frame.size.width/2
        self.profileImg.layer.borderWidth = 8.0
        self.profileImg.clipsToBounds = true
        let borderColor = UIColor.grayColor()
        self.profileImg.layer.borderColor = borderColor.CGColor
    }
    
    @IBAction func signUpPressed(sender: AnyObject) {
        let name = self.nameField.text
        let email = self.emailField.text
        let password = self.passwordField.text
        let confirmPassword = self.confirmPasswordField.text
        if password == confirmPassword {
            Bakkle.sharedInstance.account_type = Bakkle.bkAccountTypeEmail
            Bakkle.sharedInstance.localUserID(email, device_uuid: Bakkle.sharedInstance.deviceUUID, success: { () -> () in
                let fullName = split(name) {$0 == " "}
                let first_name = fullName[0]
                var last_name: String = ""
                if fullName.count == 2 {
                    last_name = fullName[1]
                }
                Bakkle.sharedInstance.facebook("", name: name, userid: Bakkle.sharedInstance.facebook_id_str, first_name: first_name, last_name: last_name, success: { () -> () in
                    Bakkle.sharedInstance.setPassword(Bakkle.sharedInstance.facebook_id_str, device_uuid: Bakkle.sharedInstance.deviceUUID, password: password, success: { () -> () in
                        Bakkle.sharedInstance.login({ () -> () in
                            if self.profileVC != nil {
                                Bakkle.sharedInstance.getAccount(Bakkle.sharedInstance.account_id, success: { (account: NSDictionary) -> () in
                                    self.profileVC!.user = account
                                    self.dismissViewControllerAnimated(true, completion: nil)
                                    if self.parentLoginInVC != nil {
                                        self.parentLoginInVC?.dismissViewControllerAnimated(false, completion: nil)
                                    }
                                    }, fail: {})
                            }else{
                                self.dismissViewControllerAnimated(true, completion: nil)
                                if self.parentLoginInVC != nil {
                                    self.parentLoginInVC?.dismissViewControllerAnimated(false, completion: nil)
                                }
                                
                            }
                        }, fail: {})
                    })
                }, fail: {() -> () in
                    var alert = UIAlertController(title: "Account exists", message: "Account already exists. Try logging in.", preferredStyle: UIAlertControllerStyle.Alert)
                    alert.addAction(UIAlertAction(title: "OK", style: UIAlertActionStyle.Default, handler: nil))
                    self.presentViewController(alert, animated: true, completion: nil)
})
            })
            
        }else{
            var alert = UIAlertController(title: "Password does not match", message: "The two password don't match", preferredStyle: UIAlertControllerStyle.Alert)
            alert.addAction(UIAlertAction(title: "OK", style: UIAlertActionStyle.Default, handler: nil))
            self.presentViewController(alert, animated: true, completion: nil)
        }
    }
    
    @IBAction func closePressed(sender: AnyObject) {
        self.dismissViewControllerAnimated(true, completion: nil)
    }
    
    func textFieldShouldReturn(textField: UITextField) -> Bool {
        textField.resignFirstResponder()
        
        return true
    }
}
