//
// MDCSwipeToChooseView.m
//
// Copyright (c) 2014 to present, Brian Gesiak @modocache
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
//

#import "MDCSwipeToChooseView.h"
#import "MDCSwipeToChoose.h"
#import "MDCGeometry.h"
#import "UIView+MDCBorderedLabel.h"
#import "UIColor+MDCRGB8Bit.h"
#import <QuartzCore/QuartzCore.h>
#import "ImageLabelView.h"


static CGFloat const MDCSwipeToChooseViewHorizontalPadding = 10.f;
static CGFloat const MDCSwipeToChooseViewTopPadding = 20.f;
static CGFloat const MDCSwipeToChooseViewLabelWidth = 65.f;

static CGFloat const ChooseItemViewImageLabelWidth = 42.f;


@interface MDCSwipeToChooseView ()
@property (nonatomic, strong) MDCSwipeToChooseViewOptions *options;
@property (nonatomic, strong) UIView *informationView;
@property (nonatomic, strong) UIView *topUserInfoView;

@end

@implementation MDCSwipeToChooseView

#pragma mark - Object Lifecycle

/*
 *              GET BACK TO THIS. THIS IS FOR THE FEED CONSTRAINTS AND UI.
 */



- (instancetype)initWithFrame:(CGRect)frame options:(MDCSwipeToChooseViewOptions *)options {
    CGRect screenBounds = [[UIScreen mainScreen] applicationFrame];
    CGFloat itemWidth = screenBounds.size.width;
    CGFloat itemHeight = screenBounds.size.height;
    
    self = [super initWithFrame:CGRectMake(0, 108, itemWidth, itemHeight-88)];
    if (self) {
        _options = options ? options : [MDCSwipeToChooseViewOptions new];
        [self setupView];
        [self constructImageView];
        [self constructLikedView];
        [self constructNopeImageView];
        [self constructHoldView];
        [self constructReportView];
       // [self constructTopUserInfoView];
        [self constructInformationView];
        [self setupSwipeToChoose];
    }
    return self;
}

#pragma mark - Internal Methods

- (void)setupView {
    self.backgroundColor = [UIColor clearColor];
    self.layer.cornerRadius = 0.f;
    self.layer.masksToBounds = YES;
    self.layer.borderWidth = 0.f;
    self.layer.borderColor = [UIColor colorWith8BitRed:220.f
                                                 green:220.f
                                                  blue:220.f
                                                 alpha:1.f].CGColor;
}

- (void)constructInformationView {
    CGFloat bottomHeight = 90.f;
    CGRect bottomFrame = CGRectMake(0,
                                    CGRectGetHeight(self.bounds) - bottomHeight,
                                    CGRectGetWidth(self.bounds),
                                    bottomHeight);
    _informationView = [[UIView alloc] initWithFrame:bottomFrame];
    
    
    _informationView.backgroundColor = [UIColor clearColor];
    _informationView.clipsToBounds = YES;
    _informationView.autoresizingMask = UIViewAutoresizingFlexibleWidth |
    UIViewAutoresizingFlexibleTopMargin;
    
    [self addSubview:_informationView];
    
    [self constructNameLabel];
    [self constructPriceLabel];
}

-(void)constructTopUserInfoView {
    CGFloat topHeight = 50.f;
    CGRect topFrame = CGRectMake(0, 0, CGRectGetWidth(self.bounds), topHeight);
    _topUserInfoView = [[UIView alloc] initWithFrame:topFrame];
    _topUserInfoView.clipsToBounds = YES;
    _topUserInfoView.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleTopMargin;
    
    UIBlurEffect *blur = [UIBlurEffect effectWithStyle:UIBlurEffectStyleDark];
    UIVisualEffectView *effectView = [[UIVisualEffectView alloc] initWithEffect:blur];
    effectView.frame = _topUserInfoView.frame;
    [_topUserInfoView addSubview:effectView];
    
    [self addSubview:_topUserInfoView];
    
}

- (void)constructNameLabel {
    CGFloat leftPadding = 0.f;
    CGFloat topPadding = 0.f;
    CGRect frame = CGRectMake(leftPadding,
                              topPadding,
                              floorf(CGRectGetWidth(_informationView.frame)),
                              CGRectGetHeight(_informationView.frame)/2);
    _nameLabel = [[UILabel alloc] initWithFrame:frame];
    
    
    
    _nameLabel.text = [NSString stringWithFormat:@"%s", ""];
    _nameLabel.font = [UIFont fontWithName:@"Avenir" size:21];
    _nameLabel.font = [UIFont boldSystemFontOfSize:25.0];
    _nameLabel.textColor = [UIColor whiteColor];
    _nameLabel.textAlignment = NSTextAlignmentCenter;
    // _nameLabel.font = [UIFont fontWithName:@"Avenir-Black" size:19];
    [_informationView addSubview:_nameLabel];
}

- (void)constructPriceLabel {
    
    CGFloat topPadding = 0.f;
    CGFloat leftPadding = 5.f;
    CGRect frame = CGRectMake(leftPadding, floorf(CGRectGetHeight(_informationView.frame)/2), floorf((CGRectGetWidth(_informationView.frame)/3)), CGRectGetHeight(_informationView.frame)/2);
    _priceLabel = [[UILabel alloc] initWithFrame:frame];
    
    
    _priceLabel.font = [UIFont fontWithName:@"Avenir" size:21];
    [_priceLabel setContentCompressionResistancePriority:800 forAxis:UILayoutConstraintAxisHorizontal];
    _priceLabel.text = [NSString stringWithFormat:@"%s", ""];
    // _priceLabel.font = [UIFont fontWithName:@"Avenir-Black" size:19];
    _priceLabel.textColor = [UIColor whiteColor];
    _priceLabel.textAlignment = NSTextAlignmentLeft;
    _priceLabel.font = [UIFont boldSystemFontOfSize:21];
    [_informationView addSubview:_priceLabel];
}

- (ImageLabelView *)buildImageLabelViewLeftOf:(CGFloat)x image:(UIImage *)image text:(NSString *)text {
    CGFloat topPadding = 17.f;
    CGRect frame = CGRectMake(x - ChooseItemViewImageLabelWidth,
                              topPadding,
                              ChooseItemViewImageLabelWidth,
                              CGRectGetHeight(_informationView.bounds));
    ImageLabelView *view = [[ImageLabelView alloc] initWithFrame:frame
                                                           image:image
                                                            text:text];
    view.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
    return view;
}

- (void)constructImageView {
    UIVisualEffect *blur;
    blur = [UIBlurEffect effectWithStyle:UIBlurEffectStyleDark];
    UIVisualEffectView *effectView;
    effectView = [[UIVisualEffectView alloc] initWithEffect:blur];
    _bottomBlurImg = [[UIImageView alloc] initWithFrame:CGRectMake(0, 0, self.bounds.size.width, self.bounds.size.height)];
    effectView.frame = _bottomBlurImg.bounds;
    [_bottomBlurImg setContentMode:UIViewContentModeScaleAspectFill];
    _bottomBlurImg.clipsToBounds = YES;
    [_bottomBlurImg addSubview:effectView];
    [self addSubview:_bottomBlurImg];
    
    _imageView = [[UIImageView alloc] initWithFrame:CGRectMake(0, 50, self.bounds.size.width, self.bounds.size.height-140)];
    [_imageView setContentMode:UIViewContentModeScaleAspectFill];
    _imageView.clipsToBounds = YES;
    [self addSubview:_imageView];
}

- (void)constructHoldView {
    CGRect frame = CGRectMake(CGRectGetMidX(_imageView.bounds)/2,
                              MDCSwipeToChooseViewTopPadding,
                              CGRectGetMidX(_imageView.bounds),
                              MDCSwipeToChooseViewLabelWidth);
    self.holdView = [[UIView alloc] initWithFrame:frame];
    [self.holdView constructBorderedLabelWithText:self.options.holdText
                                             color:self.options.holdColor
                                             angle:self.options.holdRotationAngle
                                          textSize:self.options.holdTextSize
                                                ];
    self.holdView.alpha = 0.f;
    [self.imageView addSubview:self.holdView];
}

- (void)constructReportView {
    CGRect frame = CGRectMake(CGRectGetMidX(_imageView.bounds)/2, MDCSwipeToChooseViewTopPadding, CGRectGetMidX(_imageView.bounds), MDCSwipeToChooseViewLabelWidth);
    self.reportView = [[UIImageView alloc] initWithFrame:frame];
    [self.reportView constructBorderedLabelWithText:self.options.reportText
                                              color:self.options.reportColor
                                              angle:self.options.reportRotationAngle
                                           textSize:self.options.reportTextSize
        ];
    
    self.reportView.alpha =  0.f;
    [self.imageView addSubview:self.reportView];
}

- (void)constructLikedView {
    CGRect frame = CGRectMake(MDCSwipeToChooseViewHorizontalPadding,
                              MDCSwipeToChooseViewTopPadding,
                              CGRectGetMidX(_imageView.bounds),
                              MDCSwipeToChooseViewLabelWidth);
    self.likedView = [[UIView alloc] initWithFrame:frame];
    [self.likedView constructBorderedLabelWithText:self.options.likedText
                                             color:self.options.likedColor
                                             angle:self.options.likedRotationAngle
                                          textSize:self.options.likedTextSize
];
    self.likedView.alpha = 0.f;
    [self.imageView addSubview:self.likedView];
}

- (void)constructNopeImageView {
    CGFloat width = CGRectGetMidX(self.imageView.bounds);
    CGFloat xOrigin = CGRectGetMaxX(_imageView.bounds) - width - MDCSwipeToChooseViewHorizontalPadding;
    self.nopeView = [[UIImageView alloc] initWithFrame:CGRectMake(xOrigin,
                                                                  MDCSwipeToChooseViewTopPadding,
                                                                  width,
                                                                  MDCSwipeToChooseViewLabelWidth)];
    [self.nopeView constructBorderedLabelWithText:self.options.nopeText
                                            color:self.options.nopeColor
                                            angle:self.options.nopeRotationAngle
                                         textSize:self.options.nopeTextSize
];
    self.nopeView.alpha = 0.f;
    [self.imageView addSubview:self.nopeView];
}

- (void)setupSwipeToChoose {
    MDCSwipeOptions *options = [MDCSwipeOptions new];
    options.delegate = self.options.delegate;
    options.threshold = self.options.threshold;

    __block UIView *likedImageView = self.likedView;
    __block UIView *nopeImageView = self.nopeView;
    __block UIView *holdImageView = self.holdView;
    __block UIView *reportImageView = self.reportView;
    __weak MDCSwipeToChooseView *weakself = self;
    options.onPan = ^(MDCPanState *state) {
        if (state.direction == MDCSwipeDirectionNone) {
            likedImageView.alpha = 0.f;
            nopeImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
            reportImageView.alpha = 0.f;
        } else if (state.direction == MDCSwipeDirectionLeft) {
            likedImageView.alpha = 0.f;
            reportImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
            nopeImageView.alpha = state.thresholdRatio;
        } else if (state.direction == MDCSwipeDirectionRight) {
            likedImageView.alpha = state.thresholdRatio;
            nopeImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
            reportImageView.alpha = 0.f;
        } else if (state.direction == MDCSwipeDirectionUp) {
            reportImageView.alpha = state.thresholdRatio;
            nopeImageView.alpha = 0.f;
            likedImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
        } else if (state.direction == MDCSwipeDirectionDown) {
            holdImageView.alpha = state.thresholdRatio;
            reportImageView.alpha = 0.f;
            nopeImageView.alpha = 0.f;
            likedImageView.alpha = 0.f;
        }

        if (weakself.options.onPan) {
            weakself.options.onPan(state);
        }
    };

    [self mdc_swipeToChooseSetup:options];
}

@end
