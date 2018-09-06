# Document outlining the new build process for the analyzere-python repository
Dockerfile.base contains the base level dependencies for running the
tests against the python client.

Dockerfile is the image that inherits from the base image and runs the
actual tests, so it doesn't have to rebuild the image each time.

For creating a new baseline image, you will edit the Dockerfile.base,
when you are happy with your changes, you can then retag it as the
latest and push it to ECR. In this example we will just tag it latest,
but you could push a versioned tag up to ECR if you like.

*make your changes*
```bash
vi Dockerfile.base
```

*login to AWS*
```bash
$(aws ecr get-login --no-include-email --region us-east-1)
```

*build the image*
```bash
docker build -t analyzere-python-base:latest -f Dockerfile.base .
```

*tag the image*
```bash
docker tag analyzere-python-base:latest 612007926530.dkr.ecr.us-east-1.amazonaws.com/analyzere-python-base:latest
```

*push the image to ECR*
```bash
docker push 612007926530.dkr.ecr.us-east-1.amazonaws.com/analyzere-python-base:latest
```

Now you can use the regular Dockerfile, which will use your new base
when you execute it, without having to rebuild the prior layers.

Alternatively you can use *build/rebuild_base* to automatically build /
tag / push your new base image changes
