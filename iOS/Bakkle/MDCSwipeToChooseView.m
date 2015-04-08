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

static CGFloat const MDCSwipeToChooseViewHorizontalPadding = 10.f;
static CGFloat const MDCSwipeToChooseViewTopPadding = 20.f;
static CGFloat const MDCSwipeToChooseViewLabelWidth = 65.f;

@interface MDCSwipeToChooseView ()
@property (nonatomic, strong) MDCSwipeToChooseViewOptions *options;
@end

@implementation MDCSwipeToChooseView

#pragma mark - Object Lifecycle

/*
 *              GET BACK TO THIS. THIS IS FOR THE FEED CONSTRAINTS AND UI.
 */



- (instancetype)initWithFrame:(CGRect)frame options:(MDCSwipeToChooseViewOptions *)options {
    CGRect screenBounds = [[UIScreen mainScreen] applicationFrame];
    CGFloat itemWidth = screenBounds.size.height-250;
    CGFloat itemHeight = screenBounds.size.width+10;
    self = [super initWithFrame:CGRectMake(12, 125, itemWidth, itemHeight)];
    if (self) {
        _options = options ? options : [MDCSwipeToChooseViewOptions new];
        [self setupView];
        [self constructImageView];
        [self constructLikedView];
        [self constructNopeImageView];
        [self setupSwipeToChoose];
        [self constructHoldView];
        [self constructReportView];
    }
    return self;
}

#pragma mark - Internal Methods

- (void)setupView {
    self.backgroundColor = [UIColor clearColor];
    self.layer.cornerRadius = 5.f;
    self.layer.masksToBounds = YES;
    self.layer.borderWidth = 2.f;
    self.layer.borderColor = [UIColor colorWith8BitRed:220.f
                                                 green:220.f
                                                  blue:220.f
                                                 alpha:1.f].CGColor;
}

- (void)constructImageView {
    _imageView = [[UIImageView alloc] initWithFrame:CGRectMake(0, 0, self.bounds.size.width, self.bounds.size.height)];
    [_imageView setContentMode:UIViewContentModeScaleAspectFill];
//    _imageView.clipsToBounds = YES;
    [self addSubview:_imageView];
}

- (void)constructReportView {
    CGRect frame = CGRectMake(MDCSwipeToChooseViewHorizontalPadding,
                              MDCSwipeToChooseViewTopPadding,
                              CGRectGetMidX(_imageView.bounds),
                              MDCSwipeToChooseViewLabelWidth);
    self.reportView = [[UIView alloc] initWithFrame:frame];
    [self.reportView constructBorderedLabelWithText:self.options.reportText
                                             color:self.options.reportColor
                                             angle:self.options.reportRotationAngle];
    self.reportView.alpha = 0.f;
    [self.imageView addSubview:self.reportView];
}

- (void)constructHoldView {
    CGFloat width = CGRectGetMidX(_imageView.bounds);
  //  CGFloat xOrigin = (CGRectGetMaxX(_imageView.bounds) - width - MDCSwipeToChooseViewHorizontalPadding)/2;
    CGRect frame = CGRectMake(/*xOrigin*/MDCSwipeToChooseViewHorizontalPadding, (CGRectGetMaxY(_imageView.bounds) - MDCSwipeToChooseViewTopPadding)/*MDCSwipeToChooseViewTopPadding*/, width, MDCSwipeToChooseViewLabelWidth);
    self.holdView = [[UIImageView alloc] initWithFrame:frame];
    [self.holdView constructBorderedLabelWithText:self.options.holdText color:self.options.holdColor angle:self.options.holdRotationAngle];
    
    self.holdView.alpha =  0.f;
    [self.imageView addSubview:self.holdView];
}

- (void)constructLikedView {
    CGRect frame = CGRectMake(MDCSwipeToChooseViewHorizontalPadding,
                              MDCSwipeToChooseViewTopPadding,
                              CGRectGetMidX(_imageView.bounds),
                              MDCSwipeToChooseViewLabelWidth);
    self.likedView = [[UIView alloc] initWithFrame:frame];
    [self.likedView constructBorderedLabelWithText:self.options.likedText
                                             color:self.options.likedColor
                                             angle:self.options.likedRotationAngle];
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
                                            angle:self.options.nopeRotationAngle];
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
        } else if (state.direction == MDCSwipeDirectionLeft) {
            likedImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
            nopeImageView.alpha = state.thresholdRatio;
        } else if (state.direction == MDCSwipeDirectionRight) {
            likedImageView.alpha = state.thresholdRatio;
            nopeImageView.alpha = 0.f;
            holdImageView.alpha = 0.f;
        } else if (state.direction == MDCSwipeDirectionUp) {
            holdImageView.alpha = state.thresholdRatio;
            nopeImageView.alpha = 0.f;
            likedImageView.alpha = 0.f;            
        } else if (state.direction == MDCSwipeDirectionDown) {
            reportImageView.alpha = state.thresholdRatio;
            holdImageView.alpha = 0.f;
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
